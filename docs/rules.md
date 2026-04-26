# Rules Reference

This document describes every rule shipped with the USD linter: what each rule
detects, its severity, and how to configure it.

---

## Summary

| ID                                | Title                                                                | Severity | Category    | Context            |
| --------------------------------- | -------------------------------------------------------------------- | -------- | ----------- | ------------------ |
| `invalid_prim_name`               | Prim name must match the studio naming pattern                       | error    | naming      | always             |
| `unresolved_reference`            | Asset references must resolve to existing files                      | error    | composition | always             |
| `unresolved_payload`              | Payload files must resolve to existing files                         | error    | composition | always             |
| `unresolved_sublayer`             | Sublayer files must resolve to existing files                        | error    | composition | always             |
| `sublayer_cycle`                  | USDA-style sublayer dependency chains must not form cycles           | error    | composition | always             |
| `suspicious_over_prim`            | Over prims may indicate stale composition edits                      | warning  | structure   | always             |
| `missing_required_metadata`       | Stage must contain required metadata fields                          | error    | metadata    | always             |
| `invalid_root_prim`               | defaultPrim must reference an existing root prim                     | error    | structure   | always             |
| `max_hierarchy_depth`             | Prim hierarchy must not exceed the configured maximum depth          | error    | structure   | always             |
| `zero_or_negative_scale`          | Transform scale components must be positive non-zero values          | error    | transform   | always             |
| `nan_inf_values`                  | Transform attributes must not contain NaN or Inf values              | error    | transform   | always             |
| `singular_xform_matrix`           | Xform local matrix must not be singular                              | warning  | transform   | always             |
| `unresolved_material_target`      | material:binding targets must resolve to defined materials           | error    | shading     | always             |
| `absolute_asset_path`             | Asset paths must be relative, not absolute                           | error    | composition | always             |
| `perf001_stage_file_size`         | USD layer file size should stay under the configured budget          | warning  | performance | always             |
| `perf002_prim_count`              | USD layers should stay under the configured prim-count budget       | warning  | performance | always             |
| `perf003_payload_count`           | USD layers should stay under the configured payload-count budget    | warning  | performance | always             |
| `perf004_unused_payload`          | Authored payloads should compose into the stage                      | warning  | performance | always             |
| `rig001_has_skeleton`             | Rig must contain a Skeleton prim                                     | error    | rig         | `--task rig`       |
| `rig002_has_skel_root`            | Rig must contain a SkelRoot prim                                     | error    | rig         | `--task rig`       |
| `rig003_joint_naming`             | Joint names must match the joint naming pattern                      | warning  | rig         | `--task rig`       |
| `rig004_no_mesh_at_root`          | Rig layer must not contain Mesh prims as direct children of the root | error    | rig         | `--task rig`       |
| `rig005_duplicate_joint_names`    | Joint names within a Skeleton must be unique                         | error    | rig         | `--task rig`       |
| `model001_has_geometry`           | Model layer must contain at least one geometry prim                  | error    | model       | `--task model`     |
| `model002_lod_naming`             | LOD prim names must follow the LOD0, LOD1, ... convention            | warning  | model       | `--task model`     |
| `model003_no_lights`              | Model layer must not contain light prims                             | warning  | model       | `--task model`     |
| `model005_no_cameras`             | Model layer must not contain Camera prims                            | warning  | model       | `--task model`     |
| `anim001_has_skel_animation`      | Anim layer must contain a SkelAnimation prim                         | error    | anim        | `--task anim`      |
| `anim002_has_skel_root`           | Anim layer must contain a SkelRoot prim                              | error    | anim        | `--task anim`      |
| `anim003_no_geometry`             | Anim layer should not contain geometry prims                         | warning  | anim        | `--task anim`      |
| `layout001_has_xform_root`        | Layout layer root prim must be an Xform                              | error    | layout      | `--task layout`    |
| `layout003_has_references`        | Layout layer should contain at least one asset reference             | warning  | layout      | `--task layout`    |
| `layout004_camera_naming`         | Camera prim names must match the camera naming pattern               | warning  | layout      | `--task layout`    |
| `lookdev001_has_material`         | Lookdev layer must contain at least one Material prim                | error    | lookdev     | `--task lookdev`   |
| `lookdev002_looks_scope`          | Material prims should be grouped under a Looks Scope                 | warning  | lookdev     | `--task lookdev`   |
| `lookdev003_mesh_without_binding` | Mesh prims in lookdev layers must have a material binding            | warning  | lookdev     | `--task lookdev`   |
| `maya001_namespace_clean`         | Prim names must not contain Maya namespace separators                | error    | dcc         | `--dcc maya`       |
| `maya002_shape_node_naming`       | Mesh prim names must not end with Shape                              | warning  | dcc         | `--dcc maya`       |
| `maya004_transform_as_xform`      | Xform prims must not have Maya auto-numbered names                   | info     | dcc         | `--dcc maya`       |
| `houdini001_lopnet_prims`         | USD layer must not contain Houdini LOP network residue prims         | warning  | dcc         | `--dcc houdini`    |
| `houdini002_primitive_path`       | Prim names must not look like Houdini default primitive names        | info     | dcc         | `--dcc houdini`    |
| `blender002_material_naming`      | Material prims must not use Blender default material names           | warning  | dcc         | `--dcc blender`    |
| `blender003_armature_skeleton`    | Skeleton prims must have a SkelRoot ancestor                         | warning  | dcc         | `--dcc blender`    |
| `proj001_asset_name_prefix`       | Root prim name must start with the project-configured asset prefix   | error    | project     | `--project <name>` |
| `proj002_allowed_prim_types`      | Only project-allowed prim types may be used                          | error    | project     | `--project <name>` |
| `proj004_file_naming`             | USD filename must match the project-configured naming pattern        | error    | project     | `--project <name>` |
| `proj005_forbidden_types`         | Forbidden prim types must not appear in project files                | error    | project     | `--project <name>` |

---

## Core rules (always active)

### `invalid_prim_name`

**File:** `rules/core/naming001_prim_name.py`
**Severity:** `error`

Validates that every prim name in the stage matches the studio naming pattern.
By default names must start with an uppercase letter and contain only letters,
digits, and underscores.

**Fails when:**

- The prim name does not match `rules.name_pattern`.

**Example failure:**

```usda
def Xform "myAsset" {}   # fails: starts with lowercase
def Xform "My Asset" {}  # fails: contains a space
```

**Configuration (`studio_rules.toml`):**

```toml
[rules]
name_pattern = "^[A-Z][A-Za-z0-9_]*$"
```

> Note: when a config file is present, this rule only activates if `name_pattern` appears in `[rules]`.

---

### `unresolved_reference`

**File:** `rules/core/comp001_broken_references.py`
**Severity:** `error`

Verifies that every asset reference (`@path/to/file.usda@`) points to a file
that exists on disk. References using special protocols (`://`), anonymous
paths (`anon:`), environment variables (`$`), or sublayer pointers (`<...>`)
are skipped automatically.

**Fails when:**

- The referenced file does not exist at the resolved path (relative to the
  stage directory).

**Example failure:**

```usda
def "Character" (
    references = @./rigs/hero.usda@  # fails if the file does not exist
) {}
```

**Configuration:** No dedicated parameters. Toggle via `check_references`.

---

### `suspicious_over_prim`

**File:** `rules/core/struct001_suspicious_over.py`
**Severity:** `warning`

Detects `over` prims that look poorly justified. The current heuristic flags
two cases:

- an `over` in a layer that has no references, payloads, or sublayers,
- an empty `over` with no metadata, attributes, or authored descendants.

**Fails when:**

- The `over` lives in a layer without obvious composition arcs.
- The `over` is empty and authors no useful content.

**Example failure:**

```usda
over "Character" {}   # warning: empty override with no clear composition base
```

**Configuration:** Toggle via `check_suspicious_over`.

**Current limits:**

- The check is still heuristic; it does not yet resolve whether the `over`
  truly has a valid base across every composed layer in the stage.

---

### `unresolved_payload`

**File:** `rules/core/comp002_broken_payloads.py`
**Severity:** `error`

Verifies that payloads (`payload` / `payloads`) point to files that exist on
disk.

**Fails when:**

- The file referenced by a payload does not exist at the resolved path.

**Configuration:** No dedicated parameters.

---

### `unresolved_sublayer`

**File:** `rules/core/comp003_broken_sublayers.py`
**Severity:** `error`

Verifies that `subLayers` entries point to files that exist on disk.

**Fails when:**

- The file referenced by `subLayers` does not exist at the resolved path.

**Configuration:** No dedicated parameters.

---

### `sublayer_cycle`

**File:** `rules/core/comp004_sublayer_cycle.py`
**Severity:** `error`

Detects cycles in `subLayers` chains for USDA-style files readable as text.
The check walks sublayer dependencies and reports whenever a layer transitively
depends on itself.

**Fails when:**

- `A.usda` includes `B.usda` as a sublayer and `B.usda` includes `A.usda` again.
- Any transitive `subLayers` chain closes a cycle.

**Current limits:**

- Covers `subLayers` cycles only. General cycles across `references`,
  `payloads`, and other composition arcs are not detected yet.

**Configuration:** No dedicated parameters.

---

### `missing_required_metadata`

**File:** `rules/core/meta001_missing_metadata.py`
**Severity:** `error`

Checks that the stage carries the required metadata fields in its header. By
default only `defaultPrim` is required.

**Fails when:**

- A field listed in `rules.required_stage_metadata` is missing.

**Auto-fix:** When the missing field is `defaultPrim` and the layer has
exactly one defined root prim, `--fix` writes that prim as the default.

**Example failure:**

```usda
#usda 1.0
(
    upAxis = "Y"
    # fails: defaultPrim is missing
)
```

**Configuration (`studio_rules.toml`):**

```toml
[rules]
required_stage_metadata = ["defaultPrim", "upAxis"]
```

> Note: when a config file is present, this rule only activates if `required_stage_metadata` appears in `[rules]`.

---

### `invalid_root_prim`

**File:** `rules/core/struct002_invalid_root_prim.py`
**Severity:** `error`

Validates three things about the layer's root (top-level) prims:

1. At least one root prim exists.
2. Every root prim's name is in the allowed set.
3. The header `defaultPrim` value matches an existing root prim.

**Fails when:**

- No root prim exists in the layer.
- A root prim has a name outside the allowed set.
- `defaultPrim` points to a prim that does not exist.

**Example failure:**

```usda
#usda 1.0
(
    defaultPrim = "Hero"
)
def Xform "Character" {}  # fails: "Character" not in allow-list
                           # fails: defaultPrim "Hero" does not match any root prim
```

**Configuration (`studio_rules.toml`):**

```toml
[rules]
allowed_root_prims = ["Asset", "Root", "World"]
```

> Note: when a config file is present, this rule only activates if `allowed_root_prims` appears in `[rules]`.

---

### `max_hierarchy_depth`

**File:** `rules/core/struct003_max_hierarchy_depth.py`
**Severity:** `error`

Reports any prim whose hierarchy depth exceeds `rules.max_hierarchy_depth`
(default `8`). Used to keep stages browsable and avoid runaway nesting.

**Configuration (`studio_rules.toml`):**

```toml
[rules]
max_hierarchy_depth = 12
```

---

### `zero_or_negative_scale`

**File:** `rules/core/xform001_zero_or_negative_scale.py`
**Severity:** `error` (zero scale) / `warning` (negative scale)

Detects prims whose `xformOp:scale` has zero or negative components. Zero
scale collapses geometry to a plane; negative scale silently flips normals
and usually indicates a broken export.

**Fails when:**

- Any `xformOp:scale` component is exactly `0` (error).
- Any component is negative (warning).

**Example failure:**

```usda
def Xform "Asset" {
    double3 xformOp:scale = (0, 1, 1)   # error: collapses on X
}
def Xform "Flipped" {
    double3 xformOp:scale = (-1, 1, 1)  # warning: flips normals
}
```

---

### `nan_inf_values`

**File:** `rules/core/xform002_nan_inf_values.py`
**Severity:** `error`

Detects `nan`, `inf`, or `-inf` (case-insensitive) values in any `xformOp:*`
attribute. These values crash many renderers and usually indicate broken
exports from the source DCC.

**Fails when:**

- An `xformOp:*` attribute contains the literal `nan`, `inf`, or `-inf`.

**Example failure:**

```usda
def Xform "Asset" {
    double3 xformOp:translate = (nan, 0, 0)
    double3 xformOp:scale = (1, inf, 1)
}
```

---

### `singular_xform_matrix`

**File:** `rules/core/xform003_singular_matrix.py`
**Severity:** `warning`

Consumes `SemanticStage` to flag xform stacks whose composed world matrix is
singular (determinant near zero). Singular matrices collapse geometry and
usually indicate redundant scale ops or zero components in `xformOpOrder`.

**Fails when:**

- The composed world matrix has a determinant near `0` and the stack does not
  already report `NaN`/`Inf` (which `nan_inf_values` covers).

---

### `unresolved_material_target`

**File:** `rules/core/mat001_unresolved_material_target.py`
**Severity:** `error`

Consumes `SemanticStage.material_bindings`. Reports `material:binding`
relationships pointing to prims that are not defined materials in the layer.

**Fails when:**

- Any binding target path is not present among the layer's defined prims.

**Example failure:**

```usda
def Mesh "Body" {
    rel material:binding = </Asset/Looks/MissingMat>   # error: target prim not authored
}
```

---

### `absolute_asset_path`

**File:** `rules/core/comp005_absolute_asset_path.py`
**Severity:** `error`

Detects absolute paths in `references`, `payloads`, and `subLayers`. Absolute
paths are not portable across machines (other artists, render farms, OSes)
and break composition outside the original environment.

**Fails when:**

- An `AssetReference.raw_path` starts with `<letter>:/`, `<letter>:\`, `/`,
  `\\`, or `file://`.

**Example failure:**

```usda
#usda 1.0
(
    subLayers = [@/abs/posix/look.usda@]          # error: absolute POSIX path
)
def Xform "Asset" (
    prepend payload = @C:/absolute/win/body.usda@ # error: absolute Windows path
)
{
    def Mesh "Body" (
        prepend references = @file:///body.usda@  # error: file:// protocol
    )
    {}
}
```

**Fix:** rewrite the path relative to the layer, e.g. `@./assets/body.usda@`.

---

## Performance rules

These rules combine simple per-file budgets with targeted semantic checks
backed by `pxr`. They do not replace a full composition or render-cost
analysis.

### `perf001_stage_file_size`

**File:** `rules/performance/perf001_stage_file_size.py`
**Severity:** `warning`

Reports when the USD file exceeds `rules.max_stage_file_size_bytes`.

### `perf002_prim_count`

**File:** `rules/performance/perf002_prim_count.py`
**Severity:** `warning`

Reports when the parsed prim count exceeds `rules.max_prim_count`.

### `perf003_payload_count`

**File:** `rules/performance/perf003_payload_count.py`
**Severity:** `warning`

Reports when the authored payload count exceeds `rules.max_payload_count`.

### `perf004_unused_payload`

**File:** `rules/performance/perf004_unused_payload.py`
**Severity:** `warning`

Uses `pxr.Usd.PrimCompositionQuery` to detect authored payloads that do not
produce any composed `Pcp.ArcTypePayload`. Covers cases where the file exists
but the payload contributes no data to the stage, e.g. a missing `defaultPrim`
or an invalid prim target.

**Fails when:**

- A prim has an authored payload, but OpenUSD composes no payload arc for it.

**Example failure:**

```usda
def Xform "Asset" (
    prepend payload = @./refs/empty_payload.usda@  # file exists, but lacks defaultPrim
)
{
}
```

**Configuration (`studio_rules.toml`):**

```toml
[rules]
max_stage_file_size_bytes = 52428800
max_prim_count = 10000
max_payload_count = 100
```

---

## Task rules (`--task`)

Task rules only run when `--task <type>` is passed. They can be configured
through a `[task_<type>]` section in TOML.

### Rig (`--task rig`)

---

#### `rig001_has_skeleton`

**File:** `rules/task/rig/rig001_has_skeleton.py`
**Severity:** `error`

Verifies that the layer contains at least one `Skeleton` prim. A valid USD rig
must define the skeletal structure.

**Fails when:**

- No prim has `type_name == "Skeleton"`.

**Example failure:**

```usda
def SkelRoot "Root" {}   # fails: no Skeleton defined
```

---

#### `rig002_has_skel_root`

**File:** `rules/task/rig/rig002_has_skel_root.py`
**Severity:** `error`

Verifies that the layer contains at least one `SkelRoot` prim. The `SkelRoot`
is the required container for the skeletal hierarchy in USD.

**Fails when:**

- No prim has `type_name == "SkelRoot"`.

---

#### `rig003_joint_naming`

**File:** `rules/task/rig/rig003_joint_naming.py`
**Severity:** `warning`

Validates that joints (descendants of a `Skeleton` prim) match the configured
joint naming pattern. The default allows any letter-led alphanumeric name with
underscores.

**Fails when:**

- A descendant of a `Skeleton` prim has a name that does not match the pattern.

**Example failure:**

```usda
def Skeleton "Skeleton" {
    def "_badJoint" {}   # fails: starts with underscore
}
```

**Configuration (`studio_rules.toml`):**

```toml
[task_rig]
joint_name_pattern = "^[a-zA-Z][a-zA-Z0-9_]*$"
```

---

#### `rig004_no_mesh_at_root`

**File:** `rules/task/rig/rig004_no_mesh_at_root.py`
**Severity:** `error`

Detects `Mesh` prims that are direct children of the root prim (depth 2). In a
rig, geometry should live under a SkelRoot or Xform, not directly under the
root.

**Fails when:**

- A `Mesh` prim sits at depth 2 (direct child of the root).

**Example failure:**

```usda
def Xform "Asset" {
    def Mesh "body_geo" {}   # fails: Mesh directly under root
}
```

---

#### `rig005_duplicate_joint_names`

**File:** `rules/task/rig/rig005_duplicate_joint_names.py`
**Severity:** `error`

Detects duplicate joint names within a `Skeleton`'s `joints` attribute. Even if
the full paths are unique (e.g. `root/leg_l/knee` vs `root/leg_r/knee`), many
DCCs and animation tools bind by terminal name and silently collapse duplicates,
producing incorrect bindings.

**Fails when:**

- Two or more paths in `Skeleton.joints` end with the same terminal name.

**Example failure:**

```usda
def Skeleton "Skeleton" {
    uniform token[] joints = [
        "root",
        "root/leg_l/knee",
        "root/leg_r/knee"   # error: "knee" appears twice
    ]
}
```

---

### Model (`--task model`)

---

#### `model001_has_geometry`

**File:** `rules/task/model/model001_has_geometry.py`
**Severity:** `error`

Verifies that the layer contains at least one geometry prim. A model layer
must carry visible geometry.

**Detected types:** `Mesh`, `BasisCurves`, `Points`, `NurbsPatch`.

**Fails when:**

- No prim of any of the listed geometry types exists.

---

#### `model002_lod_naming`

**File:** `rules/task/model/model002_lod_naming.py`
**Severity:** `warning`

Validates that prims representing levels of detail follow the convention `LOD0`,
`LOD1`, etc. Detects any prim whose name contains "lod" (case-insensitive) and
checks for an exact `LOD<digits>` match.

**Fails when:**

- A prim with "lod" in its name does not match `^LOD\d+$`.

**Examples:**

```usda
def Mesh "lod_high" {}   # fails: does not match the pattern
def Mesh "Lod0" {}       # fails: incorrect casing
def Mesh "LOD0" {}       # ok
```

---

#### `model003_no_lights`

**File:** `rules/task/model/model003_no_lights.py`
**Severity:** `warning`

Detects lights in model layers. Model assets should not include lights; those
belong in lighting or shot layers.

**Detected types:** `DomeLight`, `DistantLight`, `SphereLight`, `RectLight`,
`DiskLight`, `CylinderLight`, `PortalLight`, `GeometryLight`.

**Fails when:**

- Any light-typed prim exists in the layer.

---

#### `model005_no_cameras`

**File:** `rules/task/model/model005_no_cameras.py`
**Severity:** `warning`

Detects cameras in model layers. Cameras do not belong in model assets.

**Fails when:**

- Any prim has `type_name == "Camera"`.

---

### Anim (`--task anim`)

---

#### `anim001_has_skel_animation`

**File:** `rules/task/anim/anim001_has_skel_animation.py`
**Severity:** `error`

Verifies that the animation layer contains at least one `SkelAnimation` prim.
This is where USD stores skeletal animation data (joints, blendshapes).

**Fails when:**

- No prim has `type_name == "SkelAnimation"`.

---

#### `anim002_has_skel_root`

**File:** `rules/task/anim/anim002_has_skel_root.py`
**Severity:** `error`

Verifies that the animation layer contains at least one `SkelRoot` prim.

**Fails when:**

- No prim has `type_name == "SkelRoot"`.

---

#### `anim003_no_geometry`

**File:** `rules/task/anim/anim003_no_geometry.py`
**Severity:** `warning`

Detects geometry in animation layers. An anim layer should hold animation
data only, not geometry (which belongs in the model layer).

**Detected types:** `Mesh`, `BasisCurves`, `Points`, `NurbsPatch`.

**Fails when:**

- Any geometry prim exists in the layer.

---

### Layout (`--task layout`)

---

#### `layout001_has_xform_root`

**File:** `rules/task/layout/layout001_has_xform_root.py`
**Severity:** `error`

Verifies that every root prim in a layout layer is an `Xform`. In layout,
assets are organized under Xforms that define their scene placement.

**Fails when:**

- Any root prim has a type other than `Xform`.

---

#### `layout003_has_references`

**File:** `rules/task/layout/layout003_has_references.py`
**Severity:** `warning`

Verifies that the layout layer references at least one external asset. A
layout without references is probably empty or incomplete.

**Fails when:**

- The stage has no asset reference (`@...@`).

---

#### `layout004_camera_naming`

**File:** `rules/task/layout/layout004_camera_naming.py`
**Severity:** `warning`

Validates that cameras in the layer match the configured naming pattern. The
default requires the prefix `cam_`.

**Fails when:**

- A `Camera` prim's name does not match the pattern.

**Example failure:**

```usda
def Camera "shotCam" {}   # fails: does not start with cam_
def Camera "cam_main" {}  # ok
```

**Configuration (`studio_rules.toml`):**

```toml
[task_layout]
camera_name_pattern = "^cam_[a-zA-Z0-9_]+$"
```

---

### Lookdev (`--task lookdev`)

---

#### `lookdev001_has_material`

**File:** `rules/task/lookdev/lookdev001_has_material.py`
**Severity:** `error`

Verifies that the lookdev layer contains at least one `Material` prim. A
lookdev layer must define materials.

**Fails when:**

- No prim has `type_name == "Material"`.

---

#### `lookdev002_looks_scope`

**File:** `rules/task/lookdev/lookdev002_looks_scope.py`
**Severity:** `warning`

Verifies that materials are organized under a `Scope` named `Looks` or
`looks`. This is the standard USD convention for grouping materials.

**Fails when:**

- Materials exist but no `Scope` named `Looks` or `looks` is present.
- A material lives outside any Looks scope.

**Correct example:**

```usda
def Scope "Looks" {
    def Material "HeroMat" {}
}
```

---

#### `lookdev003_mesh_without_binding`

**File:** `rules/task/lookdev/lookdev003_mesh_without_binding.py`
**Severity:** `warning`

Detects `Mesh` prims with no declared `material:binding` relationship. In a
lookdev layer every visible mesh should have an explicitly assigned material.

**Fails when:**

- A `Mesh` lacks the `material:binding` attribute on its relationships.

**Example failure:**

```usda
def Xform "Asset" {
    def Scope "Looks" {
        def Material "Body_MAT" {}
    }
    def Mesh "Body" {}   # warning: no material:binding
    def Mesh "BoundBody" {
        rel material:binding = </Asset/Looks/Body_MAT>   # ok
    }
}
```

**Fix:** add `rel material:binding = </path/to/Material>` to the mesh.

---

## DCC rules (`--dcc`)

DCC rules only run when `--dcc <name>` is passed. They detect tool-specific
artifacts that often cause pipeline issues.

### Current focus per DCC

- **Maya:** export hygiene. Current rules target leaked namespaces, `Shape`
  suffixes, and auto-numbered names like `pCube1`.
- **Houdini:** Solaris/LOP residue and default naming. Current rules look for
  internal prims like `lopnet` and generic names like `geo1`.
- **Blender:** authoring defaults and basic USD Skel hygiene. Current rules
  look for `Material.001` materials and `Skeleton` prims without `SkelRoot`.

### Current limits

- Real cross-DCC round-trip is not validated.
- Tool-specific shading graphs are not inspected.
- Functional equivalence between export and import is not checked.
- Rules are pipeline heuristics: they target frequent and cheap-to-detect
  errors, not exhaustive compatibility.

### Maya (`--dcc maya`)

---

#### `maya001_namespace_clean`

**File:** `rules/dcc/maya/maya001_namespace_clean.py`
**Severity:** `error`

Detects Maya namespaces in prim names. Maya frequently exports prims in the
form `namespace:PrimName`; colons are invalid in USD paths and must be removed
before publishing.

**Fails when:**

- `prim.name` contains `:`.

**Example failure:**

```usda
def Mesh "hero:body_geo" {}   # fails: unstripped Maya namespace
```

---

#### `maya002_shape_node_naming`

**File:** `rules/dcc/maya/maya002_shape_node_naming.py`
**Severity:** `warning`

Detects the `Shape` suffix on `Mesh` prims, which Maya appends automatically
to its shape nodes. In USD this suffix is redundant and pollutes the
hierarchy.

**Fails when:**

- A `Mesh` prim's name ends with `Shape`.

**Example failure:**

```usda
def Mesh "body_geoShape" {}   # fails: Maya Shape suffix
```

---

#### `maya004_transform_as_xform`

**File:** `rules/dcc/maya/maya004_transform_as_xform.py`
**Severity:** `info`

Detects Maya auto-generated names on `Xform` prims. Maya generates names like
`pCube1`, `nurbsCircle3`, `locator2` that point to geometry that was never
renamed.

**Detected pattern:** `^[a-z][A-Za-z]+\d+$` (lowercase letter, mixed letters,
ends in digits).

**Fails when:**

- An `Xform` prim's name matches the auto-name pattern.

**Examples:**

```usda
def Xform "pCube1" {}       # fails: Maya auto-name
def Xform "locator2" {}     # fails: Maya auto-name
```

---

### Houdini (`--dcc houdini`)

---

#### `houdini001_lopnet_prims`

**File:** `rules/dcc/houdini/houdini001_lopnet_prims.py`
**Severity:** `warning`

Detects Houdini LOP network residue in the exported layer. Prims with paths
that contain `/lopnet` or names that start with `lop_` are internal Houdini
artifacts and should not ship.

**Fails when:**

- `prim.path` (lower-cased) contains `/lopnet`.
- `prim.name` starts with `lop_`.

---

#### `houdini002_primitive_path`

**File:** `rules/dcc/houdini/houdini002_primitive_path.py`
**Severity:** `info`

Detects Houdini auto-generated primitive names. Houdini generates names like
`geo1`, `sphere2`, `box3` that indicate geometry never renamed for pipeline.

**Detected pattern:** `^[a-z]+\d+$` (lowercase letters followed by digits).

**Fails when:**

- `prim.name` matches the pattern.

**Examples:**

```usda
def Mesh "geo1" {}     # fails: Houdini auto-name
def Xform "box3" {}    # fails: Houdini auto-name
```

---

### Blender (`--dcc blender`)

---

#### `blender002_material_naming`

**File:** `rules/dcc/blender/blender002_material_naming.py`
**Severity:** `warning`

Detects materials using Blender's default name. Blender creates materials
named `Material`, `Material.001`, `Material.002`, etc., which signal assets
that were never named properly.

**Detected pattern:** `^Material(\.\d{3})?$`.

**Fails when:**

- A material is named `Material` or `Material.001`, `Material.002`, etc.

---

#### `blender003_armature_skeleton`

**File:** `rules/dcc/blender/blender003_armature_skeleton.py`
**Severity:** `warning`

Verifies that every `Skeleton` prim has a `SkelRoot` ancestor. Blender
sometimes exports Skeletons without the required SkelRoot container from the
USD Skel spec.

**Fails when:**

- A `Skeleton` prim has no `SkelRoot` in any of its ancestor paths.

---

## Project rules (`--project`)

Project rules activate with `--project <name>` and require a `[project_rules]`
section in the TOML config. Each rule only runs if its corresponding key is
present and non-empty in that section.

---

### `proj001_asset_name_prefix`

**File:** `rules/project/proj001_asset_name_prefix.py`
**Severity:** `error`

Validates that every root prim's name starts with the project-configured
asset prefix. Useful for enforcing show-wide naming conventions.

**Fails when:**

- A root prim's name does not start with `asset_prefix`.

**Configuration (`studio_rules.toml`):**

```toml
[project_rules]
asset_prefix = "HERO_"
```

---

### `proj002_allowed_prim_types`

**File:** `rules/project/proj002_allowed_prim_types.py`
**Severity:** `error`

Restricts which prim types are allowed in the project. Only activates if
`allowed_prim_types` is defined and non-empty in `[project_rules]`.

**Fails when:**

- A prim's `type_name` is not in the allow-list.

**Configuration (`studio_rules.toml`):**

```toml
[project_rules]
allowed_prim_types = ["Xform", "Mesh", "Material", "Scope", "Skeleton", "SkelRoot"]
```

---

### `proj004_file_naming`

**File:** `rules/project/proj004_file_naming.py`
**Severity:** `error`

Validates that the USD filename (without extension) matches the configured
project regex.

**Fails when:**

- The filename stem does not full-match `file_name_pattern`.

**Configuration (`studio_rules.toml`):**

```toml
[project_rules]
file_name_pattern = "^[a-z][a-z0-9_]*$"
```

---

### `proj005_forbidden_types`

**File:** `rules/project/proj005_forbidden_types.py`
**Severity:** `error`

Forbids specific prim types in the project. Complementary to `proj002`; while
`proj002` defines an allow-list, `proj005` defines a deny-list. Only activates
if `forbidden_prim_types` is defined and non-empty.

**Fails when:**

- A prim's `type_name` is in the deny-list.

**Configuration (`studio_rules.toml`):**

```toml
[project_rules]
forbidden_prim_types = ["DistantLight", "DomeLight"]
```

---

## Global configuration

### `fail_on` — failure threshold

Controls the severity at which the linter returns exit code 1:

| Value | Behavior |
|-------|----------|
| `none` | Never fails (report-only). |
| `info` | Fails on any finding. |
| `warning` | Fails on warnings or errors. |
| `error` | Fails only on errors (default). |

```toml
[lint]
fail_on = "warning"
```

Or via CLI: `usd-linter file.usda --fail-on warning`.

---

### `disabled_rules` — disable rules by ID

Any rule can be explicitly disabled by its `rule_id`:

```toml
[rules]
disabled_rules = ["suspicious_over_prim", "maya004_transform_as_xform"]
```

---

### `check_references` / `check_suspicious_over`

The two highest-cost core rules can be disabled with simple booleans:

```toml
[rules]
check_references = false       # disables unresolved_reference
check_suspicious_over = false  # disables suspicious_over_prim
```

---

### `max_hierarchy_depth`

Maximum prim hierarchy depth (default `8`). The core rule `max_hierarchy_depth`
flags any prim whose depth exceeds this value.

```toml
[rules]
max_hierarchy_depth = 12
```

---

### Performance budgets

Drive `perf001_stage_file_size`, `perf002_prim_count`, and
`perf003_payload_count`. `perf004_unused_payload` has no dedicated parameter;
it can be disabled via `disabled_rules`.

```toml
[rules]
max_stage_file_size_bytes = 52428800
max_prim_count = 10000
max_payload_count = 100
```
