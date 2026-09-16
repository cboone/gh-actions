/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the upstream source tree.
 */

// Source archives have no Git metadata. Use the pinned package version
// instead of upstream's wall-clock fallback for reproducible CLI output.
fn main() {
    let destination =
        std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap()).join("version.rs");
    let content = format!("const VERSION: &str = {:?};", env!("CARGO_PKG_VERSION"));
    std::fs::write(destination, content).expect("write version information");
    println!("cargo:rerun-if-changed=build.rs");
}
