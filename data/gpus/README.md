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
└── handheld/
    └── amd/rog_ally_z1_extreme_16gb.yaml
```

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
```

### Field reference

| Section          | Field             | Type                         | Notes |
| ---------------- | ----------------- | ---------------------------- | ----- |
| (top level)      | `id`              | text                         | Required. See [Picking the ID](#picking-the-id). |
| (top level)      | `notes`           | text                         | One or two sentences. |
| `identity`       | `name`            | text                         | Required. The retail name. |
| `identity`       | `codename`        | text                         | Chip codename, such as `AD102`. |
| `identity`       | `gpu_vendor`      | `nvidia`, `amd`, `intel`     | Required. Also the folder name. |
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
| `release`        | `msrp_history`    | list                         | Each item has `date` (`'YYYY-MM'` or `'YYYY-MM-DD'`), `price_usd`, and an optional `label`. |
| `features`       | `dlss`, `fsr`, `xess`, `av1` | text              | Quote version numbers: `'3.1'`. |
| `features`       | `outputs`         | list of text                 | One `-` line per output. |

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
Start from the matching template in [templates/](../../templates/), then run:

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

The file is in the wrong folder. It belongs at
`data/gpus/<form_factor>/<gpu_vendor>/<id>.yaml`, using the values inside the
file. The message shows the expected path.

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

The ID needs exactly one memory token, such as `16gb`, and it must equal
`memory.capacity_gb`. A different memory size is a different product, so it gets
its own file.

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

A number is outside its allowed range: `memory.capacity_gb` 1-512,
`memory.bus_width_bits` 32-512, or `power.tdp_w` 5-600. Check the units. TDP is
in watts and capacity is in GB.
