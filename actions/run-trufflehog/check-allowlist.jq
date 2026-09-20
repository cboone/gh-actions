# Match TruffleHog findings against a reviewed allowlist.
#
# Inputs, both supplied with --slurpfile so a stream of JSON values arrives as
# one array:
#   $allowlist  the caller's allowlist document, as a one-element array
#   $findings   TruffleHog's --json output, one finding per element
#
# The first output line is the machine-readable verdict the caller acts on:
#
#   status blocked=<n> findings=<m>
#
# Nothing precedes it, so no interpolated field can forge it. Every later line
# is for a human to read and carries safe metadata only. This program never
# reads Raw, RawV2, Redacted, ExtraData, StructuredData or AnalysisInfo: a
# field that is never read cannot reach the report by accident.

# Fail with a message naming the offending entry and field. Validation is
# strict in both directions, because a typo in a key would otherwise widen
# the allowlist silently: an unknown key is as fatal as a missing one.
def reject($message): error("invalid allowlist: " + $message);

def entry_keys: ["commit", "detector", "line", "path", "reason"];

# Reason, detector and path are interpolated into the report. A line break in
# one of them would let an entry write its own report lines, so they may not
# carry one.
def check_single_line($index; $field; $value):
  if ($value | test("[\\r\\n]")) then
    reject("entry \($index) field \($field) must not contain a line break")
  else . end;

def validate_entry($index):
  . as $entry
  | if type != "object" then
      reject("entry \($index) is a \(type), not an object")
    else . end
  | if keys != entry_keys then
      reject(
        "entry \($index) must have exactly the keys \(entry_keys | join(", "))"
        + "; found \(keys | join(", "))"
      )
    else . end
  | if ($entry.reason | type) != "string" or ($entry.reason | length) == 0 then
      reject("entry \($index) field reason must be a non-empty string")
    else . end
  | check_single_line($index; "reason"; $entry.reason)
  | if ($entry.detector | type) != "string" or ($entry.detector | length) == 0 then
      reject("entry \($index) field detector must be a non-empty string")
    else . end
  | check_single_line($index; "detector"; $entry.detector)
  | if ($entry.commit | type) != "string"
      or ($entry.commit | test("^[0-9a-f]{40}$") | not) then
      reject(
        "entry \($index) field commit must be 40 lowercase hexadecimal "
        + "characters, because a short SHA or a ref can come to mean "
        + "something else"
      )
    else . end
  | if ($entry.path | type) != "string" or ($entry.path | length) == 0 then
      reject("entry \($index) field path must be a non-empty string")
    else . end
  | check_single_line($index; "path"; $entry.path)
  | if ($entry.path | startswith("/")) then
      reject("entry \($index) field path must be relative to the repository root")
    else . end
  | if ($entry.path | split("/") | any(. == "..")) then
      reject("entry \($index) field path must not contain a .. segment")
    else . end
  | if ($entry.line | type) != "number"
      or ($entry.line | floor) != $entry.line
      or $entry.line < 1 then
      reject("entry \($index) field line must be an integer of at least 1")
    else . end;

def validate_allowlist:
  if length != 1 then
    reject("the file must hold exactly one JSON document; found \(length)")
  else .[0] end
  | . as $document
  | if type != "object" then
      reject("the document is a \(type), not an object")
    else . end
  | if keys != ["entries", "version"] then
      reject(
        "the document must have exactly the keys entries, version; "
        + "found \(keys | join(", "))"
      )
    else . end
  | if $document.version != 1 then
      reject("version must be 1; found \($document.version | tojson)")
    else . end
  | if ($document.entries | type) != "array" then
      reject("entries must be an array")
    else . end
  | if ($document.entries | length) == 0 then
      reject("entries must not be empty; leave the allowlist input unset instead")
    else . end
  | [
      $document.entries
      | to_entries[]
      | .key as $index
      | .value
      | validate_entry($index)
    ] as $entries
  | ($entries | map([.commit, .path, .line, .detector])) as $tuples
  | if ($tuples | unique | length) != ($tuples | length) then
      reject("two entries share the same commit, path, line and detector")
    else . end
  | $entries;

# Safe metadata only. A finding with no recognized source metadata keeps a
# null commit, which no entry can match, so it is blocked rather than skipped.
def describe:
  (.SourceMetadata.Data // {}) as $data
  | {
      detector: (.DetectorName // null),
      verified: (.Verified == true),
      commit: ($data.Git.commit // null),
      path: ($data.Git.file // $data.Filesystem.file // null),
      line: ($data.Git.line // $data.Filesystem.line // null),
    };

def matches($finding):
  .commit == $finding.commit
  and .path == $finding.path
  and .line == $finding.line
  and .detector == $finding.detector;

def render($finding):
  "detector=\($finding.detector // "none")"
  + " verified=\($finding.verified)"
  + " commit=\($finding.commit // "none")"
  + " path=\($finding.path // "none")"
  + " line=\($finding.line // "none")";

def render_entry($index; $entry):
  "entry \($index): detector=\($entry.detector)"
  + " commit=\($entry.commit)"
  + " path=\($entry.path)"
  + " line=\($entry.line)";

# `matched` records the entry a finding's tuple hit, whatever the verdict, so
# an entry that stopped a verified finding is not also reported as stale.
def verdict($entries):
  . as $finding
  | ([$entries | to_entries[] | select(.value | matches($finding))] | .[0]) as $match
  | if $finding.detector == null then
      {
        state: "blocked",
        matched: null,
        text: "blocked: \(render($finding)) (the finding carries no detector name)",
      }
    elif $finding.verified then
      {
        state: "blocked",
        matched: ($match | if . == null then null else .key end),
        text: (
          "blocked: \(render($finding)) ("
          + (if $match == null then
               "a verified finding is never allowlisted"
             else
               "entry \($match.key) matches, but a verified finding is never allowlisted"
             end)
          + ")"
        ),
      }
    elif $match != null then
      {
        state: "allowed",
        matched: $match.key,
        text: (
          "allowed: \(render($finding))"
          + " entry=\($match.key) reason=\($match.value.reason)"
        ),
      }
    else
      {
        state: "blocked",
        matched: null,
        text: "blocked: \(render($finding)) (no matching allowlist entry)",
      }
    end;

($allowlist | validate_allowlist) as $entries
| [$findings[] | describe | verdict($entries)] as $verdicts
| [$verdicts[] | select(.matched != null) | .matched] as $used
| ($verdicts | map(select(.state == "allowed")) | length) as $allowed
| ($verdicts | map(select(.state == "blocked")) | length) as $blocked
| [
    $entries
    | to_entries[]
    | .key as $index
    | select(($used | index($index)) == null)
    | "::warning::trufflehog allowlist: unused \(render_entry($index; .value))"
      + " (no finding matched; the entry may be stale)"
  ] as $unused
| ["status blocked=\($blocked) findings=\($verdicts | length)"]
  + [
      "trufflehog allowlist: \($allowed) allowed, \($blocked) blocked,"
      + " \($unused | length) of \($entries | length) entries unused"
    ]
  + ($verdicts | map(.text))
  + $unused
| .[]
