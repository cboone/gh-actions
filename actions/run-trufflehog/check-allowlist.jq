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
        + "; found \(keys | tojson)"
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
        + "found \(keys | tojson)"
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

# Finding metadata comes from the scanned repository and from TruffleHog, so
# it is not this program's to trust. Git permits a newline in a filename, and
# a rendered newline would let a finding write its own report lines, one of
# which could open with "::" and be read as a workflow command. Make CR and LF
# visible instead of emitting them.
def one_line: tostring | gsub("\r"; "\\r") | gsub("\n"; "\\n");

# Data inside a workflow command is percent-decoded by the runner, so a field
# holding the text "%0A" would become a real newline and start a second
# command even though the schema rejects an actual newline. Encode it the way
# escape_data does in the shell steps: percent first, then CR and LF.
def command_data:
  tostring | gsub("%"; "%25") | gsub("\r"; "%0D") | gsub("\n"; "%0A");

# A finding this program cannot read is not a clean finding. Reading a missing
# or non-boolean Verified as "not verified" would let an entry cover it, so
# the two fields the verdict turns on are required to be what they claim.
def validate_finding($index):
  . as $finding
  | if type != "object" then
      error("invalid findings: finding \($index) is a \(type), not an object")
    else . end
  | if ($finding.DetectorName | type) != "string"
      or ($finding.DetectorName | length) == 0 then
      error(
        "invalid findings: finding \($index) carries no DetectorName string, "
        + "so the checker cannot establish which detector reported it"
      )
    else . end
  | if ($finding.Verified | type) != "boolean" then
      error(
        "invalid findings: finding \($index) has a "
        + "\($finding.Verified | type) Verified field rather than a boolean, "
        + "so the checker cannot establish whether it was verified"
      )
    else . end;

# Safe metadata only. A finding with no recognized source metadata keeps a
# null commit, which no entry can match, so it is blocked rather than skipped.
#
# The location fields are one source's tuple, so they are read from one source
# rather than resolved field by field. A per-field fallback could pair a Git
# commit with a Filesystem path and line, yielding a tuple that describes no
# finding and that an entry written for something else could match.
def describe:
  (.SourceMetadata.Data // {}) as $data
  | ($data | has("Git")) as $git
  | ($data | has("Filesystem")) as $filesystem
  | if $git and $filesystem then
      error(
        "invalid findings: a finding carries both Git and Filesystem source "
        + "metadata, so the checker cannot establish which one locates it"
      )
    else . end
  | {
      detector: .DetectorName,
      verified: .Verified,
      commit: (if $git then ($data.Git.commit // null) else null end),
      path: (
        if $git then ($data.Git.file // null)
        elif $filesystem then ($data.Filesystem.file // null)
        else null
        end
      ),
      line: (
        if $git then ($data.Git.line // null)
        elif $filesystem then ($data.Filesystem.line // null)
        else null
        end
      ),
    };

def matches($finding):
  .commit == $finding.commit
  and .path == $finding.path
  and .line == $finding.line
  and .detector == $finding.detector;

def render($finding):
  "detector=\($finding.detector | one_line)"
  + " verified=\($finding.verified)"
  + " commit=\($finding.commit // "none" | one_line)"
  + " path=\($finding.path // "none" | one_line)"
  + " line=\($finding.line // "none" | one_line)";

# Only the unused-entry warning uses this, and that line is a workflow
# command, so its fields need command_data rather than one_line.
def render_entry($index; $entry):
  "entry \($index): detector=\($entry.detector | command_data)"
  + " commit=\($entry.commit | command_data)"
  + " path=\($entry.path | command_data)"
  + " line=\($entry.line | command_data)";

# `matched` records the entry a finding's tuple hit, whatever the verdict, so
# an entry that stopped a verified finding is not also reported as stale.
def verdict($entries):
  . as $finding
  | ([$entries | to_entries[] | select(.value | matches($finding))] | .[0]) as $match
  | if $finding.verified then
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
| [
    $findings
    | to_entries[]
    | .key as $index
    | .value
    | validate_finding($index)
    | describe
    | verdict($entries)
  ] as $verdicts
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
