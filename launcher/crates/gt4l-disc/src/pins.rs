//! The disc, CORE and ELF identities that setup verifies against. They are read from the same JSON
//! files the Python tools use (`docs/inputs/`), embedded at compile time, so there is one source.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::elf::NativePolicy;

const DISC_JSON: &str = include_str!("../../../../docs/inputs/usa-v2.00.json");
const NATIVE_JSON: &str = include_str!("../../../../docs/inputs/usa-v2.00-native.json");

/// Byte length and SHA-256 of a file or image.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Identity {
    pub size_bytes: u64,
    pub sha256: String,
}

/// Everything setup needs to know about the qualified disc.
#[derive(Clone, Debug)]
pub struct Pins {
    pub disc: Identity,
    pub core: Identity,
    pub elf: Identity,
    /// Boot path as written in `SYSTEM.CNF`'s directory, for example `/SCUS_973.28;1`.
    pub boot_path: String,
    pub serial: String,
    pub version: String,
    pub video_mode: String,
    pub policy: NativePolicy,
}

#[derive(Deserialize)]
struct DiscJson {
    disc: IdentityJson,
    files: BTreeMap<String, IdentityJson>,
    system: SystemJson,
}

#[derive(Deserialize)]
struct IdentityJson {
    size_bytes: u64,
    sha256: String,
}

#[derive(Deserialize)]
struct SystemJson {
    boot_path: String,
    serial: String,
    version: String,
    video_mode: String,
}

#[derive(Deserialize)]
struct NativeJson {
    native_elf_size: u64,
    native_elf_sha256: String,
    entry_address: u32,
    records: Vec<crate::elf::CoreRecord>,
}

impl Pins {
    /// The pins of the qualified USA v2.00 disc, from the embedded `docs/inputs` files.
    pub fn embedded() -> Result<Pins, String> {
        Self::from_json(DISC_JSON, NATIVE_JSON)
    }

    pub fn traditional_chinese() -> Result<Pins, String> {
        Self::from_json(
            include_str!("../../../../docs/inputs/cht-scaj-30007.json"),
            include_str!("../../../../docs/inputs/cht-scaj-30007-native.json"),
        )
    }

    pub(crate) fn elf_file(&self) -> &str {
        self.boot_path.trim_start_matches('/').trim_end_matches(";1")
    }

    fn from_json(disc_json: &str, native_json: &str) -> Result<Pins, String> {
        let disc: DiscJson = serde_json::from_str(disc_json).map_err(|error| error.to_string())?;
        let native: NativeJson =
            serde_json::from_str(native_json).map_err(|error| error.to_string())?;
        let core = disc
            .files
            .get("/CORE.GT4;1")
            .ok_or("Disc manifest has no CORE.GT4 entry")?;
        Ok(Pins {
            disc: Identity { size_bytes: disc.disc.size_bytes, sha256: disc.disc.sha256 },
            core: Identity { size_bytes: core.size_bytes, sha256: core.sha256.clone() },
            elf: Identity { size_bytes: native.native_elf_size, sha256: native.native_elf_sha256.clone() },
            boot_path: disc.system.boot_path,
            serial: disc.system.serial,
            version: disc.system.version,
            video_mode: disc.system.video_mode,
            policy: NativePolicy {
                entry_address: native.entry_address,
                native_elf_size: native.native_elf_size,
                native_elf_sha256: native.native_elf_sha256,
                records: native.records,
            },
        })
    }
}
