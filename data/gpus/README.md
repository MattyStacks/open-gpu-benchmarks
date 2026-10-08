# GPU catalog

Every graphics card, laptop GPU, and handheld that has benchmark results has its
own file here. Its `id` is the primary key: result folders under
`data/official/<id>/` and `data/community/<id>/` must use it exactly.

The ID names one **product**, not a GPU model. Two cards with the same chip but
different memory, or from different board makers, are separate entries, and
their results are never averaged together. An 8 GB and a 16 GB RTX 5060 Ti, or
a 16 GB and a 24 GB handheld, always get their own files.

## Where a file goes

```text
data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml
```

| Folder part    | Allowed values                            | Matches field                 |
| -------------- | ----------------------------------------- | ----------------------------- |
| `form_factor`  | `desktop`, `laptop`, `handheld`, `igpu`   | `classification.form_factor`  |
| `gpu_vendor`   | `nvidia`, `amd`, `intel`                  | `identity.gpu_vendor`         |
| file name      | `<id>.yaml`                               | `id`                          |

`gpu_vendor` is the company that makes the GPU chip, **not** the board partner or
the device maker. An MSI RTX card goes under `nvidia/`, and a Steam Deck or an
ROG Ally goes under `amd/`.

```text
data/gpus/
├── desktop/
│   ├── nvidia/rtx_4090_24gb_fe.yaml
│   └── amd/rx_7900_xtx_24gb_reference.yaml
├── laptop/
│   └── nvidia/rtx_4070_laptop_8gb_generic.yaml
├── handheld/
│   └── amd/rog_ally_z1_extreme_16gb.yaml
└── reference/                         shared chip specs, see below
    ├── nvidia/rtx_4090_24gb.yaml
    └── amd/z1_extreme.yaml
```

The `reference/` folder is different: it holds
[reference files](#reference-files), not products, and nothing is benchmarked
against them.

## Picking the ID

IDs are lowercase letters, digits, and single underscores. Every ID has exactly
one memory token such as `16gb`, and it must equal `memory.capacity_gb`.

| Form factor | Pattern                                         | Examples |
| ----------- | ----------------------------------------------- | -------- |
| desktop     | `<gpu_model>_<vram>gb_<brand>_<product_line>`   | `rtx_5060_ti_8gb_msi_ventus_2x_oc`, `rtx_5060_ti_16gb_asus_tuf_gaming`, `rtx_5080_16gb_fe` |
| laptop      | `<gpu_model>_<vram>gb_<oem>_<model>`            | `rtx_4070_laptop_8gb_asus_zephyrus_g14_2023`, `rtx_4070_laptop_8gb_generic` |
| handheld    | `<device>_<chip>_<ram>gb`                       | `rog_ally_z1_extreme_16gb`, `rog_ally_x_z1_extreme_24gb`, `steam_deck_oled_16gb` |
| igpu        | `<chip>_<ram>gb_...`                            | not yet defined in detail |

Rules for each part:

- **`gpu_model`** is the GPU's own name, such as `rtx_5060_ti`, `rx_9070_xt`, or
  `arc_b580`. Laptop GPUs keep the vendor's laptop name (`rtx_4070_laptop`,
  `arc_a770m`).
- **Brand.** Desktop IDs always include the board brand (`msi_`, `asus_`,
  `gigabyte_`, `sapphire_`), because product-line names such as "Gaming OC" are
  reused across brands.
- **Cards made by the GPU vendor itself** use one fixed word instead of
  `<brand>_<product_line>`:
  - `fe`: NVIDIA Founders Edition
  - `reference`: AMD's own card (sometimes called "MBA")
  - `le`: Intel Limited Edition
- **`_oc`.** Keep `oc` in the ID when the maker sells both an OC and a non-OC
  version, because their clocks differ.
- **Colors.** A white or black version with the same specs is the same product.
  Don't make a new ID for it.
- **Handheld RAM.** Handheld memory is soldered, so the RAM size is part of the
  ID and comes last. Leave out the chip only when the device was only ever sold
  with one chip (`steam_deck_oled_16gb`).
- **Laptop RAM.** Laptop system RAM can usually be upgraded, so it is **not** in
  the ID. Record it on each run under `system.memory`. The VRAM size is in the ID.
- **`_generic` (laptops only, temporary).** When the laptop model is unknown, use
  `generic` in place of `<oem>_<model>`, for example
  `rtx_4070_laptop_8gb_generic`. The checks show a warning for each one. Replace
  it with a named model whenever you know it.

### Which ID do I use?

1. Search this folder for your product. If it exists, use that ID.
2. Desktop card: write `<gpu_model>_<vram>gb_`, then the brand and the product
   line from the box, such as `msi_ventus_2x_oc`. Use `fe`, `reference`, or
   `le` for the GPU vendor's own card.
3. Laptop: write `<gpu_model>_<vram>gb_`, then the maker and the model, such as
   `lenovo_legion_pro_5_gen8`.
4. Handheld: write the device name, the chip if the device came with more than
   one, and the RAM size: `legion_go_s_z2_go_16gb`.
5. Name the file `<id>.yaml` and put it in `<form_factor>/<gpu_vendor>/`.

## What goes in a file

Only five fields are required. Add everything else you can find, and leave the
rest out. The dashboard shows `—` for anything missing.

| Required field                 | Example                     |
| ------------------------------ | --------------------------- |
| `id`                           | `rtx_5060_ti_16gb_msi_ventus_2x` |
| `identity.name`                | `MSI GeForce RTX 5060 Ti 16G Ventus 2X` |
| `identity.gpu_vendor`          | `nvidia`                    |
| `classification.form_factor`   | `desktop`                   |
| `memory.capacity_gb`           | `16`                        |

The smallest valid file:

```yaml
id: rtx_5060_ti_16gb_msi_ventus_2x
identity:
  name: MSI GeForce RTX 5060 Ti 16G Ventus 2X
  gpu_vendor: nvidia
classification:
  form_factor: desktop
memory:
  capacity_gb: 16
```

A fuller entry, using every section:

```yaml
id: rtx_4090_24gb_fe
identity:
  name: GeForce RTX 4090
  codename: AD102
  gpu_vendor: nvidia
classification:
  form_factor: desktop
  architecture: Ada Lovelace
silicon:
  process: TSMC 4N
  die_size_mm2: 608.5
  transistors_b: 76.3
  shader_cores: 16384
  rt_cores: 128
  tmus: 512
  rops: 176
memory:
  capacity_gb: 24
  type: GDDR6X
  bus_width_bits: 384
  bandwidth_gbs: 1008
clocks:
  base_mhz: 2235
  boost_mhz: 2520
  mem_mhz: 1313
power:
  tdp_w: 450
  connectors:
    - 16-pin 12VHPWR
  pcie: 4.0 x16
release:
  date: '2022-10-12'
  msrp_usd: 1599
  msrp_history:
    - date: '2022-10'
      price_usd: 1599
features:
  dlss: '3.5'
  fsr: '3.1'
  av1: encode+decode
  outputs:
    - HDMI 2.1a
    - DP 1.4a x3
notes: Flagship Ada card.
sources:
  - url: https://www.techpowerup.com/gpu-specs/geforce-rtx-4090.c3889
    title: TechPowerUp GPU Database - GeForce RTX 4090
    accessed: '2026-10-08'
```

## Reference files

Many products share one GPU. Every RTX 5060 Ti 16 GB board has the same
shader count, memory bus, and features, and the ROG Ally and Legion Go both
use the Z1 Extreme. Instead of copying those specs into every product, put
them once in a **reference file**, and point each product at it with `base`:

```text
data/gpus/reference/<gpu_vendor>/<ref_id>.yaml
```

A product with `base: <ref_id>` gets every field from the reference, and any
field the product writes itself wins. Sections merge field by field, and lists
(such as `outputs`) are replaced whole. The required fields are checked after
the merge, so a product can inherit `memory.capacity_gb` from its reference.

```yaml
# data/gpus/reference/nvidia/rtx_4090_24gb.yaml: the GPU's shared specs
id: rtx_4090_24gb
identity:
  name: GeForce RTX 4090
  codename: AD102
  gpu_vendor: nvidia
classification:
  architecture: Ada Lovelace
silicon:
  shader_cores: 16384
memory:
  capacity_gb: 24
  type: GDDR6X
clocks:
  boost_mhz: 2520
power:
  tdp_w: 450
```

```yaml
# data/gpus/desktop/nvidia/rtx_4090_24gb_fe.yaml: one card built on it
id: rtx_4090_24gb_fe
base: rtx_4090_24gb
identity:
  name: GeForce RTX 4090 Founders Edition
  gpu_vendor: nvidia
  board_partner: NVIDIA
classification:
  form_factor: desktop
power:
  connectors:
    - 16-pin 12VHPWR
release:
  date: '2022-10-12'
  msrp_usd: 1599
```

A factory-overclocked partner card would add only what differs, such as
`clocks.boost_mhz`.

What goes where:

| In the reference (the GPU)                         | In the product (what you buy)                         |
| -------------------------------------------------- | ----------------------------------------------------- |
| `identity.name` (the GPU model), `codename`, `gpu_vendor` | `identity.name` (the retail name), `gpu_vendor`, `board_partner` |
| `classification.architecture`                      | `classification.form_factor`                          |
| `silicon`, `clocks`, `power.tdp_w`, `power.pcie`   | Board differences: OC clocks, `power.connectors`      |
| `memory` (APUs: only `bus_width_bits`, `shared`)   | Handhelds: `memory.capacity_gb`, `type`, `bandwidth_gbs` |
| `features` except outputs                          | `features.outputs`, `release`, `skus`, `platform`, `notes` |

Rules for reference files:

- **Required:** `id`, `identity.name`, and `identity.gpu_vendor`.
- **ID:** `<gpu_model>_<vram>gb`, such as `rtx_5060_ti_16gb`. For an APU whose
  memory comes from the device, use the chip name with no memory token, such as
  `z1_extreme`.
- **Product-only fields aren't allowed:** `base`, `skus`, `platform`,
  `identity.board_partner`, and `classification.form_factor`.
- **Results never point at a reference.** Always benchmark against the exact
  product.
- **`base` is optional.** A product used by only one device can hold every
  field itself. `steam_deck_oled_16gb` does.

## Product-only fields

| Field                    | For              | What it is |
| ------------------------ | ---------------- | ---------- |
| `base`                   | any product      | The reference file name to inherit from. |
| `identity.board_partner` | desktop only     | Who made the board: `NVIDIA`, `MSI`, `ASUS`, `Sapphire`, ... |
| `skus`                   | any product      | Retail names or part numbers that share this entry, such as color variants. One `-` line each. |
| `platform`               | handheld, laptop | The device's own specs. See below. |

### Device specs: `platform`

Handhelds and laptops are judged by their GPU, but the rest of the device
changes the results too. A handheld with slower RAM, or a lower power limit, is
slower with the same chip. `platform` records those details. Every field is
optional:

| Field          | Type   | Example                | Notes |
| -------------- | ------ | ---------------------- | ----- |
| `oem`          | text   | `ASUS`                 | The device maker. |
| `cpu`          | text   | `Zen 4 8C/16T`         | |
| `ram_mts`      | number | `7500`                 | RAM speed in MT/s, 1000-20000. Handhelds only; laptop RAM goes on each result. |
| `os_shipped`   | text   | `Windows 11`           | The OS the device ships with. The OS you tested goes on each result. |
| `display`      | text   | `7 in 1920x1080 120 Hz` | |
| `power_min_w`, `power_max_w` | number | `9`, `30`    | APU power range (handhelds) or GPU TGP range (laptops), 1-600 W. The minimum can't exceed the maximum. |
| `battery_wh`   | number | `80`                   | 1-200 Wh. |

```yaml
platform:
  oem: Lenovo
  cpu: Zen 4 8C/16T
  ram_mts: 7500
  os_shipped: Windows 11
  display: 8.8 in QHD+ 144 Hz
  power_min_w: 9
  power_max_w: 30
```

## Sources

Every catalog file says where its specs came from, in a `sources` list. Each
item is one page, written as a `- url:` line with its fields indented below:

```yaml
sources:
  - url: https://www.techpowerup.com/gpu-specs/geforce-rtx-4090.c3889
    title: TechPowerUp GPU Database - GeForce RTX 4090
    accessed: '2026-10-08'
    covers:
      - silicon
      - memory
      - clocks
```

| Field      | Required | Format |
| ---------- | -------- | ------ |
| `url`      | yes      | An `https://` link anyone can open. |
| `title`    | no       | A short description of the page. Avoid `: ` inside it, or quote the whole title. |
| `accessed` | no       | The day you checked the page, as a quoted `'YYYY-MM-DD'`. |
| `covers`   | no       | The sections this page backs, one `-` line each: `identity`, `classification`, `silicon`, `memory`, `clocks`, `power`, `release`, `features`, `platform`. |

Guidelines:

- **Prefer pages anyone can check.** Use the maker's spec page, a vendor
  PSREF or spec sheet, or TechPowerUp's GPU database. Avoid forum posts and
  pages that need a login.
- **Cite what you used.** List only the pages the values in this file came
  from. If a value isn't backed by any source yet, leave it out of every
  `covers` list rather than guessing.
- **References and products each cite their own pages.** A product's merged
  entry in `gpus.json` lists its own sources first, then its reference's. A URL
  that both cite appears once, with both `covers` lists combined.
- **Prices can cite their own page.** An item in `release.msrp_history` can
  carry its own `source:` link, because prices often come from somewhere other
  than the spec sheet.

A file without `sources` still passes, but the checks warn about it
(`sources-missing`). That warning will become an error once every entry has
sources.

### Field reference

| Section          | Field             | Type                         | Notes |
| ---------------- | ----------------- | ---------------------------- | ----- |
| (top level)      | `id`              | text                         | Required. See [Picking the ID](#picking-the-id). |
| (top level)      | `base`            | text                         | Products only. See [Reference files](#reference-files). |
| (top level)      | `skus`            | list of text                 | Products only. |
| (top level)      | `notes`           | text                         | One or two sentences. |
| (top level)      | `sources`         | list                         | Where the specs came from. See [Sources](#sources). |
| `identity`       | `name`            | text                         | Required. The retail name. |
| `identity`       | `codename`        | text                         | Chip codename, such as `AD102`. |
| `identity`       | `gpu_vendor`      | `nvidia`, `amd`, `intel`     | Required. Also the folder name. |
| `identity`       | `board_partner`   | text                         | Desktop products only. |
| `classification` | `form_factor`     | `desktop`, `laptop`, `handheld`, `igpu` | Required. Also the folder name. |
| `classification` | `architecture`    | text                         | Such as `Ada Lovelace` or `RDNA 3`. |
| `silicon`        | `process`         | text                         | Such as `TSMC 4N`. |
| `silicon`        | `die_size_mm2`, `transistors_b`, `shader_cores`, `rt_cores`, `tmus`, `rops` | number | |
| `memory`         | `capacity_gb`     | number, 1-512                | Required. Must match the ID's `<N>gb`. |
| `memory`         | `type`            | text                         | Such as `GDDR6X` or `LPDDR5X`. |
| `memory`         | `bus_width_bits`  | number, 32-512               | |
| `memory`         | `bandwidth_gbs`   | number                       | |
| `memory`         | `shared`          | `true` or `false`            | `true` when the GPU uses system RAM (handhelds, iGPUs). |
| `clocks`         | `base_mhz`, `boost_mhz`, `mem_mhz` | number      | |
| `power`          | `tdp_w`           | number, 5-600                | Board power, or the top of the power range for laptops and handhelds. |
| `power`          | `connectors`      | list of text                 | One `-` line per connector. |
| `power`          | `pcie`            | text                         | Such as `4.0 x16`. |
| `release`        | `date`            | quoted `'YYYY-MM-DD'`        | |
| `release`        | `msrp_usd`        | number                       | |
| `release`        | `msrp_history`    | list                         | Each item has `date` (`'YYYY-MM'` or `'YYYY-MM-DD'`), `price_usd`, and optional `label` and `source` (an `https://` link). |
| `features`       | `dlss`, `fsr`, `xess`, `av1` | text              | Quote version numbers: `'3.1'`. |
| `features`       | `outputs`         | list of text                 | One `-` line per output. |
| `platform`       | see [Device specs](#device-specs-platform) | | Handheld and laptop products only. |

Any other field is rejected, so a typo can't hide.

## YAML style

Write every list item on its own line starting with `-`, the same way result
files do. Don't use inline `[ ]` or `{ }`, even for empty values. If a field has
no value, leave it out.

Wrong:

```yaml
power:
  connectors: [16-pin 12VHPWR]
features: {}
release:
  date: 2022-10-12
```

Right:

```yaml
power:
  connectors:
    - 16-pin 12VHPWR
release:
  date: '2022-10-12'
```

Quote dates and version numbers. Without quotes, YAML reads `2022-10-12` as a
date object and `3.1` as a number, and the checks reject both.

## Adding an entry

The step-by-step walkthrough is in
[CONTRIBUTING.md](../../CONTRIBUTING.md#adding-a-card-laptop-or-handheld).
Look for a reference file for your GPU under `reference/`, and create one from
`templates/catalog_reference.yaml` if it's missing and more than one product
will use it. Start the product from the matching template in
[templates/](../../templates/), then run:

```powershell
python scripts/validate.py catalog
```

## What the checks mean

`python scripts/validate.py catalog` and the **Catalog entries** check on a pull
request report every problem at once. Each message starts with the rule name in
brackets, and links here.

#### `catalog-empty`

No `.yaml` files were found under `data/gpus/`. The catalog can't be empty.

#### `yaml-invalid`

The file isn't valid YAML. Check indentation (two spaces, no tabs), and quote
values that contain `: ` or start with a special character.

#### `yaml-inline`

The file uses inline `[ ]` or `{ }`. Rewrite the value as indented lines. See
[YAML style](#yaml-style).

#### `catalog-not-mapping`

The file is empty, or it starts with `- id:` like the old single-file catalog.
Put one entry per file, with `id:` at the left margin and no leading `-`.

#### `catalog-folder`

The file is in the wrong folder. A product belongs at
`data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml` and a reference at
`data/gpus/reference/<gpu_vendor>/<id>.yaml`, using the values inside the file.
The message shows the expected path.

#### `id-filename`

The file name doesn't match the `id`. Rename the file to `<id>.yaml`, using the
`.yaml` extension.

#### `id-duplicate`

Another file already uses this `id`. Search the catalog. If it's the same
product, add results to the existing entry. If it's a different product, give it
an ID that tells the two apart.

#### `id-format`

The ID has uppercase letters, spaces, dashes, or double underscores, or it
doesn't follow the pattern for its form factor. Desktop and laptop IDs need a
model before the memory token and a board or device after it. Handheld IDs end
with the memory token. See [Picking the ID](#picking-the-id).

#### `id-memory-token`

A product ID needs exactly one memory token, such as `16gb`, and it must equal
`memory.capacity_gb`, including a capacity inherited from `base`. A different
memory size is a different product, so it gets its own file. A reference ID
may have no memory token (`z1_extreme`), but no more than one.

#### `id-generic`

As an **error**: `generic` was used on a non-laptop entry, or it doesn't replace
the whole `<oem>_<model>` part. Only laptops may use it, as
`<gpu_model>_<vram>gb_generic`.

As a **warning**: this laptop entry is a placeholder for an unknown model.
That's allowed for now. Rename it to the real laptop model when you know it, and
move its result folders to match.

#### `field-required`

One of the five required fields is missing: `id`, `identity.name`,
`identity.gpu_vendor`, `classification.form_factor`, or `memory.capacity_gb`.

#### `field-renamed`

`identity.vendor` is now `identity.gpu_vendor`. Rename the field.

#### `field-unknown`

The file has a field the catalog doesn't know about. It's usually a typo or a
field in the wrong section. Compare it with the
[field reference](#field-reference).

#### `field-type`

A value has the wrong type. The usual causes are:

- a date without quotes (`date: 2022-10-12` should be `date: '2022-10-12'`)
- a version number without quotes (`fsr: 3.1` should be `fsr: '3.1'`)
- text where a number belongs
- a list written on one line instead of as `-` lines

#### `field-value`

`gpu_vendor` or `form_factor` isn't one of the allowed values listed in
[Where a file goes](#where-a-file-goes).

#### `field-range`

A number is outside its allowed range:

| Field | Allowed range |
| ----- | ------------- |
| `memory.capacity_gb` | 1-512 GB |
| `memory.bus_width_bits` | 32-512 bits |
| `power.tdp_w` | 5-600 W |
| `platform.ram_mts` | 1000-20000 MT/s |
| `platform.power_min_w`, `platform.power_max_w` | 1-600 W |
| `platform.battery_wh` | 1-200 Wh |

The check also fails if `platform.power_min_w` is above `power_max_w`. Check
the units.

#### `field-not-allowed`

A section is on the wrong kind of product. `platform` is only for handhelds and
laptops. `identity.board_partner` is only for desktop cards. A device's maker
goes in `platform.oem`.

#### `reference-field`

A reference file has a field that belongs to a product: `base`, `skus`,
`platform`, `identity.board_partner`, or `classification.form_factor`. Move it
to the product files that use this reference.

#### `sources-missing`

This is a warning. The file has no `sources` list. Add the pages its specs came
from (see [Sources](#sources)). This will become an error once every entry has
sources.

#### `source-invalid`

A `sources` item, or a `release.msrp_history` item's `source`, is malformed. The
usual causes are:

- the `url` is missing or isn't `https://`
- `sources` is written as one line instead of `- url:` items
- a field other than `url`, `title`, `accessed`, or `covers`
- an unquoted or wrongly formatted `accessed` date (use `'2026-10-08'`)
- a `covers` entry that isn't a section name

If a `title` contains `: `, quote the whole title or use ` - ` instead.
Otherwise YAML reads it as a new field and the file fails as `yaml-invalid`.

#### `base-unknown`

`base` doesn't name a file in `data/gpus/reference/`. Check the spelling (it's
the reference's file name without `.yaml`), or add the reference file. A
product can't use another product as its base.

#### `base-mismatch`

The product's `identity.gpu_vendor` differs from its reference's. A product
always has the same GPU vendor as the chip it's built on. Fix whichever one is
wrong.
