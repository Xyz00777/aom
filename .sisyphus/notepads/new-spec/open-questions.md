# Open Questions: `nom` (nix-output-monitor) Research

## Executive Summary

`nom` (nix-output-monitor) is a Haskell TUI application that provides real-time visualization of Nix builds. It parses nix build output (either JSON or human-readable) and renders a colored, tree-based dependency graph with build progress statistics.

**Repository**: https://github.com/maralorn/nix-output-monitor  
**Primary rendering code**: `lib/NOM/Print.hs` (lines 159-712)  
**Commit**: 2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b

---

## 1. Visual Layout

### Overall Structure

Nom's UI consists of **two main sections**:

1. **Top Section**: Build logs (nix output passed through)
2. **Bottom Section**: Nom's visualization panel (dynamically updated)

The bottom panel contains:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dependency Graph:                              ┃
┃ ┏━ Builds  ━━━━ ━━ Downloads ━━ ━ Uploads ━ ━┫
┃ ┃ Running  Done  Todo   Run  Done  Run  Done ┃┃
┃ ┃   ⏵ 3     ✔ 42  ⏸ 10   ↓ ⏵ 2  ↓ ✔ 15 ↑ ⏵ 1 ┃┃
┃ ┃   [Per-host breakdown if multiple hosts]    ┃┃
┃ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃┃
┃ ┃ ┌─ Tree view of builds ───────────────────┐ ┃┃
┃ ┃ │ ⏵ package-name (phase) ∅ 3s [on host] │ ┃┃
┃ ┃ │ ├─⏵ dependency-1                       │ ┃┃
┃ ┃ │ └─✔ dependency-2 2s                    │ ┃┃
┃ ┃ │ ✔ completed-pkg 5s                     │ ┃┃
┃ ┃ │ ⏸ planned-dep                          │ ┃┃
┃ ┃ └───────────────────────────────────────┘ ┃┃
┃ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛┃
┃ ⏱ 2m34s                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Visual Components

**Source**: `lib/NOM/Print.hs` lines 60-102

#### Unicode Symbols & Colors

| Symbol | Meaning | Color |
|--------|---------|-------|
| `⏵` | Running/building | Yellow (bold) |
| `✔` | Completed/success | Green |
| `⏸` | Planned/waiting | Blue |
| `⚠` | Failed | Red |
| `↓ ⏵` | Downloading | Yellow |
| `↑ ⏵` | Uploading | Yellow |
| `↓ ✔` | Downloaded | Green |
| `↑ ✔` | Uploaded | Green |
| `↓ ⏸` | Waiting to download | Blue |
| `∅` | Average build time (mean of last 10) | Grey |
| `⏱` | Running time | Default |
| `∑` | Summary totals | Default |

#### Box Drawing Characters

| Char | Unicode | Name | Usage |
|------|---------|------|-------|
| `┃` | U+2503 | BOX DRAWINGS HEAVY VERTICAL | Vertical lines in tree |
| `┗` | U+2517 | BOX DRAWINGS HEAVY UP AND RIGHT | Bottom corners |
| `┏` | U+250F | BOX DRAWINGS HEAVY DOWN AND RIGHT | Top corners |
| `┣` | U+2523 | BOX DRAWINGS HEAVY VERTICAL AND RIGHT | Section divider |
| `━` | U+2501 | BOX DRAWINGS HEAVY HORIZONTAL | Horizontal lines |

**Evidence**: [Print.hs lines 60-102](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L60-L102)

---

## 2. Summary/Dashboard View

### Summary Table

Nom displays a **compact summary table** at the top of its visualization:

**Source**: `lib/NOM/Print.hs` lines 205-237

```
┏━━━━━━━┓
┃ Builds ┃ Downloads ┃ Uploads ┃ Host              ┃
┃ ⏵  ✔  ⏸ ┃ ⏵  ✔  ⏸  ┃ ⏵  ✔   ┃                   ┃
┃ 3  42 10 ┃ 2  15   5 ┃ 1  8    ┃ build.example.com ┃
┗━━━━━━━━━┛
```

**Structure** (from lines 213-237):

```haskell
headers =
  (cells 3 <$> optHeader showBuilds "Builds")
    <> (cells 3 <$> optHeader showDownloads "Downloads")
    <> (cells 2 <$> optHeader showUploads "Uploads")
    <> optHeader showHosts "Host"
```

**Columns**:
- **Builds**: Running (`⏵`), Completed (`✔`), Planned (`⏸`)
- **Downloads**: Running (`↓ ⏵`), Completed (`↓ ✔`), Planned (`↓ ⏸`)
- **Uploads**: Running (`↑ ⏵`), Completed (`↑ ✔`)
- **Host**: Remote builder hostname (shown only when multiple hosts)

### Per-Host Breakdown

When using remote builders or multiple substituters, nom shows per-host statistics:

**Source**: [Print.hs lines 271-306](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L271-L306)

```
Host: build.example.com (ec)
  ⏵ 2   ✔ 15  ⏸ 5   ↓ ⏵ 1  ↓ ✔ 8
```

**Host Abbreviation Algorithm** ([lines 321-350](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L321-L350)):
- Tries to create collision-free abbreviations from hostname
- Example: `build.example.com` → `ec` (uses last parts before TLD)
- Shows `(protocol)` suffix for non-standard protocols (e.g., `ssh-ng`)

### Total vs Per-Host Display Logic

**Source**: [Print.hs lines 239-250](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L239-L250)

```haskell
showHosts = Set.size hosts > 1
manyHosts = Set.size buildHosts > 1 || Set.size hosts > 2
```

- Shows per-host breakdown if >1 unique host
- Shows host labels if using remote builders OR >2 transfer peers

---

## 3. Tree vs Summary View

### Both Are Displayed Simultaneously

Nom shows **BOTH** the dependency tree AND the summary table, not one or the other.

**Layout**: [Print.hs lines 173-192](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L173-L192)

```haskell
sections =
  fmap snd
    . filter fst
    $ [
        (not (Seq.null nixErrors), const errorDisplay)
      , (not (Seq.null nixTraces), const traceDisplay)
      , (not (Seq.null forestRoots), buildsDisplay . snd)
      ]

-- ... then later ...
printSections . one . table . time
```

**Rendering Order**:
1. Errors (if any) - shown first
2. Traces (if any) - shown second
3. Dependency tree (if builds running) - shown third
4. Summary table (always shown at bottom)
5. Elapsed time (always at end)

### Tree Visibility Logic

**Source**: [Print.hs lines 407-433](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L407-L433)

```haskell
derivationsToShow :: DerivationSet
derivationsToShow =
  let should_be_shown (index, (can_be_hidden, _, _)) = not can_be_hidden || index < limits.height
```

The tree is **shown if there are builds in progress**. Otherwise, only the summary + elapsed time show.

### Tree Display Algorithm

**Adaptive rendering** ([lines 407-475](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L407-L475)):

1. Takes terminal height/width into account
2. Targets tree to fill ~1/3 of terminal height (`targetRatio = 3`)
3. Prioritizes showing:
   - Failed builds (always shown)
   - Running builds (always shown)
   - Running downloads/uploads (shown if relevant)
   - Dependencies of above
4. Uses smart sorting to show most relevant nodes
5. Avoids duplicates - each derivation appears once at lowest level

---

## 4. Activity View (Currently Running)

### Running Activities Display

Nom shows **currently running builds/downloads/uploads** in the dependency tree with live status:

**Source**: [Print.hs lines 549-646](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L549-L646)

#### Running Build Display

```
⏵ package-name (build-phase) on buildhost ∅ 3s
```

**Components**:
- `⏵` - Yellow, bold (running indicator)
- `package-name` - Derivation name (yellow, bold)
- `(build-phase)` - Current phase in parentheses, bold (optional, JSON mode only)
- `on hostname` - Remote host if not localhost (magenta)
- `∅ 3s` - Average build time estimate from cache (grey)

**Build time estimation**: Uses mean of last 10 builds of derivations with same name.

**Phase information**: Only available in JSON mode (`--json` flag). Can show phases like:
- `unpacking sources`
- `patching sources`
- `configuring`
- `building`
- `installing`

**Evidence**: [Print.hs lines 607-619](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L607-L619)

```haskell
Building buildInfo ->
  let phaseList = case phaseMay buildInfo.activityId of
        Nothing -> []
        Just phase -> [markup bold ("(" <> phase <> ")")]
      before_time =
        [markups [yellow, bold] (running <> " " <> drvName)]
          <> hostMarkup True buildInfo.host
          <> phaseList
      after_time = Strict.maybe [] (\x -> ["(" <> average <> " " <> timeDiffSeconds x <> ")"]) buildInfo.estimate
```

#### Running Download/Upload Display

```
↓ ⏵ output-name from cache.nixos.org 5.2s 234.5MiB/1.2GiB [████████░░░░░░░░░░░░] 19.5%
```

**Components**:
- `↓ ⏵` / `↑ ⏵` - Yellow, bold (download/upload indicator)
- `output-name` - Store path name (yellow, bold)
- `from hostname` / `to hostname` - Transfer peer (magenta)
- `5.2s` - Elapsed time (shown if > 1s)
- `234.5MiB/1.2GiB` - Transfer progress
- Progress bar (shown when size known)

**Progress bar** ([lines 649-662](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L649-L662)):

```haskell
printBar :: Int -> Double -> Text
printBar len part = toText bar
 where
  pct :: Double
  pct = part * intToDouble len
  bar :: String
  bar =
    [1, 2 .. intToDouble len] <&> \case
      ((<= pct + 0 / 2) -> True) -> '■'
      ((<= pct + 1 / 2) -> True) -> '◧'
      _ -> '□'
```

Characters: `■` (filled), `◧` (partial), `□` (empty)

### Failed Build Display

**Source**: [Print.hs lines 620-634](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L620-L634)

```
⚠ package-name on remote-host failed with exit code 1 after ⏱ 45s (configurePhase)
```

- Red, bold
- Shows failure type: `exit code N` or `hash mismatch`
- Shows duration
- Shows phase if available

### Completed Build Display

**Source**: [Print.hs lines 635-646](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L635-L646)

```
✔ package-name on localhost 5s
```

- Green checkmark
- Shows host and time (if > 1s)

---

## 5. Statistics Shown

### Time Statistics

**Elapsed Time**: [Print.hs line 196-199](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L196-L199)

```haskell
time
  | progressState == Finished = \(nowClock, now) -> 
      finishMarkup (" at " <> toText (formatTime defaultTimeLocale "%H:%M:%S" nowClock) <> " after " <> runTime now)
  | otherwise = \(_, now) -> clock <> " " <> runTime now
```

**Format**: [Print.hs lines 702-709](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L702-L709)

```haskell
printDuration :: NominalDiffTime -> Text
printDuration diff
  | diff < minute = p "%Ss"
  | diff < hour = p "%Mm%Ss"
  | diff < day = p "%Hh%Mm%Ss"
  | otherwise = p "%dd%Hh%Mm%Ss"
```

Formats: `< 1m: "23s"`, `< 1h: "5m30s"`, `< 1d: "2h15m30s"`, `>= 1d: "1d2h15m30s"`

### Build Statistics

**Source**: [Print.hs lines 251-259](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L251-L259)

```haskell
numRunningBuilds = CMap.size runningBuilds
numCompletedBuilds = CMap.size completedBuilds
numPlannedBuilds = CSet.size plannedBuilds
totalBuilds = numPlannedBuilds + numRunningBuilds + numCompletedBuilds
downloadsDone = CMap.size completedDownloads
downloadsRunning = CMap.size runningDownloads
uploadsRunning = CMap.size runningUploads
uploadsDone = CMap.size completedUploads
```

**Shows**:
- Running builds count (`⏵ N`)
- Completed builds count (`✔ N`)  
- Planned builds count (`⏸ N`)
- Running downloads (`↓ ⏵ N`)
- Completed downloads (`↓ ✔ N`)
- Planned downloads (`↓ ⏸ N`)
- Running uploads (`↑ ⏵ N`)
- Completed uploads (`↑ ✔ N`)

### Download/Upload Sizes

**Source**: [Print.hs lines 664-682](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L664-L682)

```haskell
printTransferProgress :: [ActivityProgress] -> (Maybe Double, [Text])
printTransferProgress = \case
  [] -> (Nothing, [])
  ap ->
    ( Just $ intToDouble done' / intToDouble expected
    , [printBytes done' <> "/" <> printBytes expected]
    )

printBytes :: Int -> Text
printBytes bytes = fromString $ printf "%.1f%s" res unit
 where
  (res, unit) = fromMaybe (start, "") $ find ((< 1000) . fst) (zip scaled sizes)
  start = intToDouble bytes
  scaled = start : ((/ 1024) <$> scaled)

sizes :: [Text]
sizes = "B" : ((<> "iB") <$> ["K", "M", "G", "T", "P"])
```

**Formats**: Uses IEC units: `B`, `KiB`, `MiB`, `GiB`, `TiB`, `PiB`

### Build Rate / ETA

**NOTE**: Nom does **NOT currently show**:
- ❌ Build rate (builds/second)
- ❌ Time remaining (ETA)
- ❌ Percentage of total builds completed

**Evidence**: Checked all of `Print.hs` - no rate or ETA calculations found.

The only time estimate shown is `∅` (average build time for same derivation type, from historical cache).

**Related Open Issue**: [#255](https://github.com/maralorn/nix-output-monitor/issues/255) - FR to show cumulative estimated time in tree

---

## 6. Compact Mode

**Nom does NOT have different display modes** (verbose vs compact).

**However, it has adaptive display** based on:

### Terminal Size Adaptation

**Source**: [Print.hs lines 182-184](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L182-L184)

```haskell
maxWindow = case maybeWindow of
  Just (Window height width) -> Window (height `div` targetRatio) (width - 2)
  Nothing -> Window.Window defaultTreeMax (defaultTreeWidth - 2)
```

Defaults: `defaultTreeMax = 20`, `defaultTreeWidth = 60`, `targetRatio = 3`

### Time Threshold Filtering

**Source**: [Print.hs lines 367-368](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L367-L368)

```haskell
ifTimeDurRelevant :: NominalDiffTime -> ([Text] -> [Text]) -> [Text]
ifTimeDurRelevant dur mod' = memptyIfFalse (dur > 1) (mod' [clock, printDuration dur])
```

**Only shows times > 1 second** to reduce clutter.

### Related Open Issue

[#225](https://github.com/maralorn/nix-output-monitor/issues/225) - Keybinds to hide the tree, resize the log area (enhancement, not yet implemented)

---

## 7. Source Code Analysis

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `exe/Main.hs` | Entry point, command handling, signal handlers | 251 |
| `lib/NOM/Print.hs` | **Main rendering logic** | 712 |
| `lib/NOM/Print/Table.hs` | Table formatting utilities | 185 |
| `lib/NOM/Print/Tree.hs` | Tree rendering logic | 29 |
| `lib/NOM/State.hs` | State types (BuildStatus, DerivationInfo, etc.) | 404 |
| `lib/NOM/Update.hs` | State update logic | 562 |
| `lib/NOM/IO.hs` | Input/output handling | - |
| `lib/NOM/NixMessage/JSON.hs` | JSON parser | - |

### Data Flow

```
Nix Output (JSON/OldStyle)
    ↓
NOM.IO.Input (Parser)
    ↓
NOM.Update (State Transition)
    ↓
NOM.State (NOMState)
    ↓
NOM.Print (Rendering)
    ↓
Terminal Output
```

### State Types

**BuildStatus** ([State.hs lines 140-146](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/State.hs#L140-L146)):

```haskell
data BuildStatus
  = Unknown       -- Not yet seen
  | Planned       -- Queued for build
  | Building (BuildInfo ())
  | Failed (BuildInfo BuildFail)
  | Built (BuildInfo Double)
```

**DependencySummary** ([State.hs lines 168-178](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/State.hs#L168-L178)):

```haskell
data DependencySummary = MkDependencySummary
  { plannedBuilds :: DerivationSet
  , runningBuilds :: DerivationMap RunningBuildInfo
  , completedBuilds :: DerivationMap CompletedBuildInfo
  , failedBuilds :: DerivationMap FailedBuildInfo
  , plannedDownloads :: StorePathSet
  , completedDownloads :: StorePathMap CompletedTransferInfo
  , completedUploads :: StorePathMap CompletedTransferInfo
  , runningDownloads :: StorePathMap RunningTransferInfo
  , runningUploads :: StorePathMap RunningTransferInfo
  }
```

### Rendering Key Functions

```haskell
-- Main entry point
stateToText :: Config -> NOMState -> Maybe (Window Int) -> (ZonedTime, Double) -> Text

-- Tree rendering
printBuilds :: NOMState -> Map Text Text -> Window Int -> Double -> NonEmpty Text

-- Dependency tree
printTreeNode :: TreeLocation -> DerivationInfo -> Double -> (Text, Maybe Double)

-- Derivation display
printDerivation :: DerivationInfo -> Map Text StorePathId -> (Bool, Double -> Text, Double -> Maybe Double)

-- Table
table :: (ZonedTime, Double) -> Text
```

### Per-Derivation Display Logic

**Source**: [Print.hs lines 515-646](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L515-L646)

The `printDerivation` function uses pattern matching on `BuildStatus`:

1. **Downloading**: Shows progress bar, bytes transferred, hostname
2. **Uploading**: Similar to download
3. **Unknown + planned download**: Shows waiting state
4. **Unknown + downloaded**: Shows completed with size and time
5. **Unknown + uploaded**: Similar
6. **Unknown (default)**: Just shows derivation name
7. **Planned**: Shows with `⏸` prefix, blue
8. **Building**: Shows phase, host, time estimate
9. **Failed**: Shows error type, duration, phase
10. **Built**: Shows completion time

---

## 8. Comparison with `nix build`

### Plain `nix build` Output

```
building '/nix/store/xxx-package-name.drv'...
configure: configuring...
build: building...
install: installing...
```

**Characteristics**:
- Linear log output
- No summary
- No progress indication
- Hard to see overall state
- Mixed stdout/stderr
- No dependency visualization

### `nom build` Output

**Advantages**:
- ✅ Dependency tree visualization
- ✅ Build summary with counts
- ✅ Progress bars for downloads
- ✅ Phase information (JSON mode)
- ✅ Build time estimates from cache
- ✅ Errors/traces highlighted
- ✅ Per-host breakdown for remote builds
- ✅ Colored status indicators
- ✅ Concurrent build visualization
- ✅ Transfer progress (bytes uploaded/downloaded)

**Data Sources**:

**Source**: README.md

```
Right now nom uses four sources of information:
1. The parsed nix-build output (json or human-readable)
2. it checks if build results exist in the nix-store (only human-readable mode)
3. it queries `.drv` files for information about the `out` output path.
4. It caches build times in `$XDG_CACHE_HOME/nix-output-monitor/build-reports.csv`.
```

### JSON Mode vs Human-Readable Mode

**JSON Mode** (`--json` flag):
- Much more information available
- Can show build phases
- Can show download/upload progress
- Requires `--log-format internal-json -v`

**Human-Readable Mode**:
- Works with any nix command
- Less information available
- Can't detect download completion (nix limitation)
- Must check store for completion

**Evidence**: [README.md limitations section](https://github.com/maralorn/nix-output-monitor/blob/main/README.md)

---

## Open Questions for Our Implementation

### Q1: Should we replicate the tree view?

**Considerations**:
- Tree view requires maintaining full dependency graph
- Complex state management (DerivationInfo, StorePathInfo)
- Smart filtering to fit terminal height
- Tree reordering based on activity

**Alternative**: Show flat list of running builds with summary

### Q2: How to handle remote builders?

Nom tracks:
- Localhost builds
- Builds on each remote host
- Downloads from each substituter/cache
- Uploads to each cache

**Data**: Per-host counters, host abbreviations, protocol display

### Q3: Phase information availability

**Nom can show phases only in JSON mode** - this requires parsing nix's internal JSON log format.

Do we have access to phase information from `deno` / `npm` builds?

### Q4: Time estimation algorithm

Nom uses `$XDG_CACHE_HOME/nix-output-monitor/build-reports.csv` to store historical build times.

**Question**: Should we implement similar caching? Or derive from first principles?

### Q5: Concurrent vs Sequential Display

Nom shows **concurrent builds** in tree, but our `deno` + `deno-task` + `deno-check` + `npm` + `ansible` runs are **sequential phases**.

Should we adapt the UI for sequential phases instead of a tree?

### Q6: Error/Trace Display

Nom collects errors and traces and displays them in a dedicated section:

**Source**: [Print.hs lines 128-154](https://github.com/maralorn/nix-output-monitor/blob/2e5180152e621ad7e0c0b66ccaa81c82ceab7f2b/lib/NOM/Print.hs#L128-L154)

Should we collect and display errors/traces similarly?

### Q7: Progress Bar Implementation

Nom's progress bar:
- Only shown for transfers with known sizes
- Uses Unicode block characters: `■`, `◧`, `□`
- Shows percentage: `19.5%`

Should we implement progress bars for our builds?

### Q8: Terminal Size Handling

Nom gracefully handles:
- Missing terminal size info
- Small terminals (defaults to 20 lines, 60 columns)
- Resizing

Do we need to handle this?

---

## Key Implementation Insights

### 1. State is the Core

Nom's `NOMState` type tracks:
- All derivation info (name, outputs, status, dependencies)
- Build summary (planned/running/completed/failed counts)
- Store path states (downloaded/uploaded/planned)
- Activities (phases, progress)
- Errors/traces

### 2. Render is Pure

`stateToText` is a pure function:
```haskell
stateToText :: Config -> NOMState -> Maybe (Window Int) -> (ZonedTime, Double) -> Text
```

State is maintained separately, rendering just formats current state.

### 3. Smart Tree Pruning

The tree is aggressively pruned to fit terminal:
- Prioritizes running/failed builds
- Hides nodes that can be hidden
- Shows lowermost dependencies
- Uses intelligent sorting

### 4. Minimal Dependencies

Uses standard Haskell libraries:
- `ansi-terminal` for colors
- `terminfo` for terminal size detection
- No external TUI framework

### 5. Streaming Architecture

Input is processed as stream:
- Each line parsed
- State updated
- Rerender triggered
- Efficient handling of long builds

---

## References

- **Repository**: https://github.com/maralorn/nix-output-monitor
- **README**: https://github.com/maralorn/nix-output-monitor/blob/main/README.md
- **Print.hs**: https://github.com/maralorn/nix-output-monitor/blob/main/lib/NOM/Print.hs
- **State.hs**: https://github.com/maralorn/nix-output-monitor/blob/main/lib/NOM/State.hs
- **Demo (Remote Build)**: https://asciinema.org/a/KwCh38ujQ9wusHw8kyW4KCMZo
- **Demo (Downloads)**: https://asciinema.org/a/7hJXH2iFLEkKxG1lL25lspqNn
- **Latest Release**: v2.1.8 (2025-11-08)


---

## NEW QUESTIONS - nom-style Compact View Design (2026-04-20)

### PQ1: What is nom's actual layout? What sections does it show?

- **Context**: User wants a nom-style compact view as the DEFAULT view for AOM. Need to understand nom's actual UI structure to replicate for Ansible.

- **Evidence from nom Source Code** (`/tmp/nix-output-monitor/lib/NOM/Print.hs`):

  **nom's Layout Structure**:
  
  From `stateToText` function (lines 159-172), nom renders these sections:
  
  ```
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┃ ⏱ 2m34s                                                   
  ┃ ━━ Dependency Graph with 3 roots:                          
  ┃ ┃   ⏵ running package-a-1.0                                  
  ┃ ┃   ⏸ package-b-2.0                                          
  ┃ ┃   ✔ package-c-3.0                                          
  ┃ ┗━━━ ⏵ building package-d-4.0 (buildhost)                   
  ┣━━━ ∑ Builds │ Downloads │ Uploads │ Host                     
  ┃      ⏵ 2   │ ⏵ ↓1     │ ⏵ ↑0  │ localhost               
  ┃      ✔ 5   │ ✔ ↓3     │ ✔ ↑0  │ build.example.com       
  ┃      ⏸ 10  │ ⏸ ↓5     │        │                           
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```
  
  **Key Components**:
  
  1. **Timer Line** (top):
     - Shows elapsed time with ⏱ icon
     - Example: `⏱ 2m34s` 
     - On finish: Shows timestamp + total duration
   
  2. **Dependency Graph Section** (main area):
     - Title: `━━ Dependency Graph:`
     - Tree structure showing derivations (Nix build units)
     - Each node shows: status icon + derivation name + timing
     - Status icons:
       - `⏵` (yellow): running builds
       - `✔` (green): completed builds
       - `⏸` (blue): planned builds (waiting)
       - `⚠` (red): failed builds
       - `↓ ⏵`: running downloads
       - `↑ ⏵`: running uploads
   
  3. **Summary Table** (bottom):
     - Rows per host (localhost + remote builders)
     - Columns:
       - Builds: running (⏵), completed (✔), planned (⏸)
       - Downloads: running (↓⏵), completed (↓✔), planned (↓⏸)
       - Uploads: running (↑⏵), completed (↑✔)
       - Host name
   
  4. **Error Display** (conditional):
     - Shows `⚠ N Errors:` with error details
     - Compact error display (truncates verbose errors)
  
  **nom's Key Innovation**:
  
  From nom README:
  > "While your build runs, nom will draw something like this **at the bottom of your build log**"
  
  **CRITICAL INSIGHT**: nom is NOT a full-screen TUI! It's a **compact status widget** that appears at the BOTTOM of the terminal, while build logs scroll above it.
  
  **nom Display Mode**:
  - nom uses ANSI cursor manipulation to:
    1. Keep itself at the bottom of the terminal
    2. Let normal build output scroll above
    3. Updates in-place (not full redraw)
  
  **How nom renders** (from Print.hs, lines 186-191):
  ```haskell
  buildsDisplay now =
    prependLines
      horizontal -- "━"
      (vertical <> " ")  -- "┃ "
      (vertical <> " ")  -- "┃ "
      (printBuilds buildState hostAbbrevs maxWindow now)
  ```
  
  Uses **box-drawing characters** for the frame:
  - `┏` (upper left)
  - `┣` (left T)
  - `┗` (lower left)
  - `┃` (vertical)
  - `━` (horizontal)

- **Options for AOM**:
  
  A) **Exact nom-style (compact status at bottom)**
     - Layout: Streaming logs above + compact status at bottom
     - Status: Play/task tree + per-host stats
     - Like: `ansible-playbook output...` (scrolling)
            `┏━━ AOM Status ━━━━━━━━━━━━━━━` (fixed at bottom)
            `┃ ⏵ Task 3/10: Install nginx`
            `┃ web1: ✔5 ⚡2 ❌0 | db1: ✔3 ⚡0 ❌1`
            `┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`
     - Pro: Minimal screen real estate
     - Pro: Can still read full logs
     - Con: Requires ANSI cursor management (tricky)
     - Con: Not a traditional Textual TUI (just ANSI rendering)
  
  B) **Two-panel TUI (logs + status side-by-side)**
     - Layout: Left panel (logs) + Right panel (status tree)
     - Like lazydocker, htop
     - Pro: Textual-native (panels, widgets)
     - Pro: Can have keyboard interactions
     - Con: Uses full screen (not compact)
     - Con: Not nom-style (it's a full TUI)
  
  C) **Hybrid: Compact mode + Optional full TUI**
     - Default: Compact nom-style (option A)
     - With `--tui` flag: Full Textual TUI (option B)
     - Pro: Best of both worlds
     - Pro: nom-style by default (familiar to users)
     - Pro: Full TUI when needed (interactive features)
     - Con: Two implementations to maintain

- **Recommendation**: **Option C (Hybrid)** because:
  - Matches user requirement: "DEFAULT view nom-style, `aom --tui` for full TUI"
  - nom users expect compact status at bottom
  - Full TUI adds: keyboard navigation, search, expand/collapse
  - Implementation approach:
    - **Compact mode**: Use Rich/RichLog with ANSI positioning (no Textual)
    - **Full TUI mode**: Use Textual App with panels

### PQ2: How does nom show currently running items?

- **Context**: nom's key innovation is showing what's happening NOW (running builds). Need to understand how to show "currently running tasks" for Ansible.

- **Evidence from nom Source Code**:

  **nom's Running Build Display** (lines 607-618 in Print.hs):
  
  ```haskell
  Building buildInfo ->
    let phaseList = case phaseMay buildInfo.activityId of
          Nothing -> []
          Just phase -> [markup bold ("(" <> phase <> ")")]
        before_time =
          [markups [yellow, bold] (running <> " " <> drvName)]
            <> hostMarkup True buildInfo.host
            <> phaseList
        after_time = Strict.maybe [] (\x -> ["(" <> average <> " " <> timeDiffSeconds x <> ")"]) buildInfo.estimate
      in ( False
          , \now -> unwords $ before_time <> ifTimeDiffRelevant now buildInfo.start (<> after_time)
          , const Nothing
          )
  ```
  
  **Format**: `⏵ derivation-name on hostname (phase) (duration) (∅ estimate)`
  
  **Example Output**:
  ```
  ⏵ package-a-1.0 on buildhost (building) (5s) (∅ 10s)
  ```
  
  **Key Features**:
  
  1. **Status Icon**: Always first (`⏵` for running)
  2. **Derivation Name**: The build target
  3. **Host**: `on hostname` if remote
  4. **Phase**: `(phase-name)` if available (only for local builds)
  5. **Duration**: Shows elapsed time if >1s
  6. **Estimate**: Shows `∅` (average) from historical builds
  
  **nom's Dependency Graph Relevance**:
  
  From nom README:
  > "nom will try to show you the most relevant part of the dependency tree, roughly aiming to fill a third of your terminal"
  
  **Algorithm** (lines 407-474 in Print.hs):
  
  ```haskell
  derivationsToShow :: DerivationSet
  derivationsToShow =
    let should_be_shown (index, (can_be_hidden, _, _)) = not can_be_hidden || index < limits.height
        (_, sorted_set) = execState (goDerivationsToShow forestRoots) mempty
      in CSet.fromFoldable
          $ fmap (\(_, (_, _, drvId)) -> drvId)
          $ takeWhile should_be_shown
          $ itoList
          $ Set.toAscList sorted_set
  ```
  
  **Showing Logic**:
  1. Always show running/failed builds (highest priority)
  2. Show tree structure only for relevant portion
  3. Limit to ~1/3 of terminal height
  4. Hide intermediate nodes if they don't add information
  
  **For Ansible adaptation**:
  
  Instead of "currently building derivations", show:
  - Currently running tasks (per host)
  - Currently blocked tasks (waiting for other hosts)
  - Task name + host + duration
  
  **Example AOM format**:
  ```
  ┃ ━━ Running Tasks:
  ┃ ⏵ web1: Install nginx (5s)
  ┃ ⏵ web2: Configure firewall (2s)
  ┃ ⏸ web3: Waiting for web1 (blocked)
  ```

- **Recommendation for AOM**:
  
  **Currently Running Section**:
  - Show all currently running tasks (one per line)
  - Format: `⏵ hostname: task-name (duration)`
  - Group by play (optional)
  - Show blocked tasks with `⏸` icon
  
  **Implementation**:
  ```python
  # In state management
  def get_currently_running(self) -> dict[str, list[TaskState]]:
      """Get all currently running tasks, grouped by host."""
      running = {}
      for play in self.plays.values():
          for task in play.tasks.values():
              if task.status == Status.RUNNING:
                  for host, host_state in task.hosts.items():
                      if host_state.status == Status.RUNNING:
                          if host not in running:
                              running[host] = []
                          running[host].append(task)
      return running
  
  # In render function
  def render_running_section(state: RunState) -> list[str]:
      """Render currently running tasks."""
      lines = ["━━ Currently Running:"]
      running = state.get_currently_running()
      
      for host, tasks in running.items():
          for task in tasks:
              duration = task.duration or 0
              icon = "⏵"
              line = f"┃ {icon} {host}: {task.name} ({format_duration(duration)})"
              lines.append(line)
      
      return lines if len(lines) > 1 else []
  ```

### PQ3: How to show per-host stats summary in compact mode?

- **Context**: nom shows per-host build stats at the bottom. Need similar for Ansible: per-host task stats.

- **Evidence from nom Source Code**:

  **nom's Host Summary Table** (lines 271-306 in Print.hs):
  
  ```haskell
  printHosts :: [NonEmpty Entry]
  printHosts =
    mapMaybe (nonEmpty . labelForHost)
      $ sortOn (fmap (reverse . Text.splitOn ".") . preview #_Hostname)
      $ toList
      $ Set.map forgetProto hosts
    where
      labelForHost :: Host WithoutContext -> [Entry]
      labelForHost host =
        showCond
          showBuilds
          [ yellow $ nonZeroShowBold running numRunningBuildsOnHost
          , green $ nonZeroShowBold done doneBuilds
          , dummy
          ]
          <> showCond
            showDownloads
            [ yellow $ nonZeroShowBold down downloadsRunning'
            , green $ nonZeroShowBold down downloads
            , dummy
            ]
          <> showCond
            showUploads
            [ yellow $ nonZeroShowBold up uploadsRunning'
            , green $ nonZeroShowBold up uploads
            ]
          <> one (magenta . header $ host_name_cell host)
  ```
  
  **Table Layout**:
  
  ```
  │ ⏵ │ ✔ │ ⏸ │ ↓⏵ │ ↓✔ │ ↓⏸ │ ↑⏵ │ ↑✔ │ Host
  ├───┼───┼───┼─────┼─────┼─────┼─────┼─────┼─────┤
  │ 2 │ 5 │ 10│  1  │  3  │  5  │  0  │  0  │ localhost
  │ 1 │ 3 │ 5 │  0  │  2  │     │     │     │ buildhost
  ```
  
  **Key Features**:
  
  1. **Per-host rows**: Each host gets a row
  2. **Icon + count**: Each column has icon prefix (e.g., `⏵ 2`)
  3. **Non-zero highlight**: Bold if count > 0
  4. **Host abbreviation**: Uses `collisionFreeHandles` to create short aliases
  
  **For Ansible adaptation**:
  
  Instead of builds/downloads/uploads, show:
  - OK (✔): Successful tasks
  - Changed (⚡): Tasks that made changes
  - Failed (❌): Failed tasks
  - Unreachable (⚠): Unreachable hosts
  - Skipped (⊘): Skipped tasks
  
  **Example AOM format**:
  
  ```
  ┣━━━ Host Summary
  ┃ ✔ │ ⚡ │ ❌ │ ⚠ │ Host
  ┃ 5 │ 2 │ 0 │ 0 │ web1
  ┃ 5 │ 1 │ 1 │ 0 │ web2
  ┃ 3 │ 0 │ 0 │ 0 │ db1
  ```
  
  **Icon Mapping**:
  ```python
  STATUS_ICONS = {
      "ok": ("✔", "green"),
      "changed": ("⚡", "yellow"),
      "failed": ("❌", "red"),
      "unreachable": ("⚠", "red"),
      "skipped": ("⊘", "grey"),
      "running": ("⏵", "blue"),
      "pending": ("⏸", "grey"),
  }
  ```
  
  **Implementation**:
  
  ```python
  def render_host_summary(state: RunState) -> str:
      """Render per-host stats summary."""
      lines = []
      
      # Header
      lines.append("┣━━━ Host Summary")
      lines.append("┃ ✔ │ ⚡ │ ❌ │ ⚠ │ Host")
      
      # Per-host rows
      for host, stats in state.host_stats.items():
          ok = stats.get("ok", 0)
          changed = stats.get("changed", 0)
          failed = stats.get("failed", 0)
          unreachable = stats.get("unreachable", 0)
          
          # Color: red if failed/unreachable, yellow if changed, green if ok
          if failed > 0 or unreachable > 0:
              color = "red"
          elif changed > 0:
              color = "yellow"
          else:
              color = "green"
          
          line = f"┃ {ok:2} │ {changed:2} │ {failed:2} │ {unreachable:2} │ {host}"
          lines.append(colorize(line, color))
      
      return "\n".join(lines)
  ```

- **Recommendation for AOM**:
  
  **Host Summary Section**:
  - Show as last section in compact status (bottom)
  - Format: Table with columns for each status type
  - Color rows based on worst status (failed > unreachable > changed > ok)
  - Show all hosts that have started at least one task
  
  **Alternative: Compact Line Format**:
  
  For very compact output (like user example):
  
  ```
  web1: ✔5 ⚡2 ❌0 | db1: ✔3 ⚡0 ❌1
  ```
  
  This format is more compact but loses visual alignment.

### PQ4: How to create Textual single-panel compact view that looks like streaming terminal?

- **Context**: User wants compact view to still be a Textual app (for password modal, crash detection). But it should look like streaming terminal output, not a multi-panel TUI.

- **Evidence from Textual Documentation**:

  **Textual Inline Mode**:
  
  From Textual blog post "Behind the Curtain of Inline Terminal Applications":
  
  - **Inline apps**: Appear under the prompt, not full-screen
  - **Use case**: `textual run --pipe` for non-interactive mode
  - **Limitation**: Still uses full Textual rendering engine
  
  **RichLog for Streaming Output**:
  
  From Textual docs:
  - `RichLog` is a scrollable widget for logging
  - Can append lines in real-time
  - Supports Rich renderables (formatted text, tables, etc.)
  - Has `auto_scroll` to follow new output
  
  **Example: Single-Panel Streaming App**:
  
  ```python
  from textual.app import App, ComposeResult
  from textual.widgets import RichLog, Footer
  from rich.text import Text
  
  class CompactStreamApp(App):
      """Single-panel streaming output app."""
      
      CSS = """
      RichLog {
          height: 100%;
      }
      """
      
      def compose(self) -> ComposeResult:
          yield RichLog(id="output", highlight=True, markup=True)
          yield Footer()
      
      async def on_mount(self):
          log = self.query_one(RichLog)
          
          # Stream output
          async for line in stream_ansible_output():
              log.write(line)
  ```
  
  **Problem**: This is a full-screen TUI, not nom-style compact status.
  
  **Solution: Non-TUI mode for compact**:
  
  For nom-style compact output, we need to **NOT use Textual** for the compact view:
  
  - Use **Rich/ANSI directly** for compact mode
  - Use **Textual** only for:
    - Password modals (suspend compact mode, show modal)
    - Error dialogs (when crash detected)
    - Full TUI mode (with `--tui` flag)

- **Architecture Recommendation**:

  **Two Rendering Backends**:
  
  ```python
  # aom/renderer.py
  
  class CompactRenderer:
      """ANSI-based compact renderer (nom-style)."""
      
      def __init__(self, state: RunState):
          self.state = state
          self.last_render_time = 0
      
      def render(self) -> str:
          """Render compact status to string."""
          lines = []
          
          # Timer line
          lines.append(f"⏱ {format_duration(self.state.elapsed_time)}")
          
          # Currently running
          lines.extend(self.render_running())
          
          # Host summary
          lines.extend(self.render_host_summary())
          
          # Frame it with box-drawing chars
          return self.frame(lines)
      
      def frame(self, lines: list[str]) -> str:
          """Add box-drawing frame around content."""
          width = max(len(line) for line in lines)
          framed = [f"┏{'━' * (width + 2)}┓"]
          for line in lines:
              framed.append(f"┃ {line:<{width}} ┃")
          framed.append(f"┗{'━' * (width + 2)}┛")
          return "\n".join(framed)
      
      def update_display(self):
          """Update terminal display (ANSI cursor manipulation)."""
          now = time.time()
          if now - self.last_render_time < 0.1:  # 10 FPS max
              return
          
          output = self.render()
          
          # Move cursor to bottom of screen
          # Clear lines used by previous render
          # Write new output
          # (This is the tricky part - need ANSI cursor commands)
          pass
  
  
  class TUIRenderer(App):
      """Textual-based TUI renderer (full mode)."""
      
      def compose(self):
          yield TreePanel(id="tree")
          yield LogPanel(id="log")
          yield StatusBar(id="status")
      
      def update_state(self, state: RunState):
          """Update TUI widgets with new state."""
          tree = self.query_one("#tree")
          tree.update_state(state)
  ```
  
  **Integration**:
  
  ```python
  # aom/cli.py
  
  def main():
      args = parse_args()
      
      if args.tui:
          # Full TUI mode
          app = TUIRenderer()
          app.run()
      else:
          # Compact mode (nom-style)
          renderer = CompactRenderer(state)
          
          # Stream ansible-playbook output
          async for event in stream_ansible():
              state.handle_event(event)
              renderer.update_display()
              print(event.raw_line)  # Print raw output above status
  ```

- **Recommendation for AOM**:
  
  **Architecture**:
  - **Compact mode**: ANSI rendering (no Textual)
    - Use Rich Console for formatting
    - Manual ANSI cursor positioning for fixed bottom status
    - Handle password prompts by suspending output, showing prompt inline
  
  - **TUI mode**: Full Textual TUI
    - Panels: tree, log, status
    - Keyboard navigation, search, expand/collapse
    - Integrated password modal
  
  **Why this approach**:
  - nom style REQUIRES non-TUI rendering (fixed position at bottom)
  - Textual is designed for full-screen TUIs, not compact status bars
  - Password modal: In compact mode, pause rendering, let ansible-playbook handle prompt inline
  - Crash detection: Wrap main() in try/except, show error on crash

### PQ5: How to show progress through play/task tree in compact mode?

- **Context**: User asked about showing "collapsed version of the tree inline". Need to show progress through the play/task structure in compact form.

- **Evidence from nom Source Code**:

  **nom's Tree Rendering**:
  
  nom shows a dependency TREE, not flat list:
  
  ```
  ┃ ━━ Dependency Graph with 3 roots:
  ┃ ┃   ⏵ package-a-1.0
  ┃ ┃   ┏━ ⏸ package-b-2.0
  ┃ ┃   ┃   └━ ✔ package-c-3.0
  ┃ ┗━━━ ⏵ building package-d-4.0
  ```
  
  Uses `Tree` structure from `Data.Tree` with custom rendering.
  
  **For Ansible**:
  
  Ansible playbooks are NOT trees - they're sequential:
  - Play 1 → Task 1, Task 2, Task 3
  - Play 2 → Task 4, Task 5
  
  **Progress Display Options**:
  
  A) **Progress Bar** (linear)
     ```
     ┃ Play 1/3 ████████░░ 8/10 tasks
     ```
     - Pro: Simple, clear progress
     - Con: Doesn't show tree structure
  
  B) **Collapsed Tree** (show current play only)
     ```
     ┃ ━━ Play 2: Configure Webservers
     ┃ ┃   ✔ Install nginx
     ┃ ┃   ⏵ Configure firewall (running)
     ┃ ┃   ⏸ Restart nginx
     ```
     - Pro: Shows tree structure
     - Con: Only shows current play
  
  C) **Summary Statistics**
     ```
     ┃ Plays: 1/3 │ Tasks: 8/24 │ Hosts: web1, web2, db1
     ```
     - Pro: Compact, informative
     - Con: No visual progress
  
  D) **Multi-level Progress**
     ```
     ┃ ▶ Play 2/3: Configure Webservers
     ┃   ⏵ Task 8/24: Configure firewall (web1 running, web2 done)
     ```
     - Pro: Shows both play and task progress
     - Con: Verbose

- **Recommendation for AOM**:

  **Hybrid Approach** (collapsible in TUI, compact in default):
  
  **Compact Mode**:
  ```
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ┃ ⏱ 2m34s                                       
  ┃ ━━ Play 2/3: Configure Webservers             
  ┃ ⏵ web1: Configure firewall (5s)              
  ┃ ⏵ web2: Install nginx (2s)                   
  ┣━━━ Hosts                                      
  ┃ web1: ✔5 ⚡2 ❌0 | web2: ✔3 ⚡0 ❌1           
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```
  
  **Full TUI Mode**:
  - Expandable tree showing all plays/tasks
  - Click/Enter to expand/collapse roles
  - Shows full history (completed tasks grayed out)

### PQ6: How should compact view behave when stdout is not a TTY?

- **Context**: When piping output (e.g., `aom site.yml | grep ERROR`), need to decide: fall back to plain text, or use ANSI formatting?

- **Evidence from nom Source Code**:

  **nom's Behavior**:
  
  From nom README:
  > "In human-readable log mode you can preserve the color of the redirected text by using the `unbuffer` command from the `expect` package."
  
  nom detects TTY and behaves differently:
  - TTY: Uses ANSI colors and cursor positioning
  - Non-TTY: Still uses ANSI colors (but no cursor positioning)
  
  **Textual's Behavior**:
  
  From Textual docs:
  - Textual apps require TTY
  - If run with `--pipe` or non-TTY stdout, Textual will error
  
  **Best Practices for CLI Tools**:
  
  1. **Detect TTY**: `sys.stdout.isatty()`
  2. **No colors if not TTY**: `--no-color` or `NO_COLOR` env var
  3. **Force color**: `--color` or `FORCE_COLOR` env var
  
  **From click/typer libraries**:
  ```python
  import sys
  import os
  
  def should_use_color() -> bool:
      """Determine if color output should be used."""
      # Force color
      if os.environ.get('FORCE_COLOR'):
          return True
      
      # No color
      if os.environ.get('NO_COLOR'):
          return False
      
      # Check TTY
      return sys.stdout.isatty()
  ```

- **Recommendation for AOM**:
  
  **Non-TTY Behavior**:
  
  1. **No ANSI cursor positioning**: Just print lines sequentially (no fixed bottom status)
  2. **Keep ANSI colors** (respect `NO_COLOR` env var)
  3. **Print summary at end**: Instead of live updates, show final summary
  
  **Example**:
  
  ```bash
  # Interactive TTY (default)
  $ aom site.yml
  [streaming output with live status at bottom]
  
  # Piped output
  $ aom site.yml | grep ERROR
  ERROR: Task failed on web2: Configure firewall
  ERROR: Host unreachable: db1
  
  # Final summary printed at end
  PLAY RECAP ****
  web1: ok=5 changed=2 failed=0
  web2: ok=3 changed=0 failed=1
  db1: ok=0 changed=0 failed=0 unreachable=1
  ```
  
  **Implementation**:
  
  ```python
  class CompactRenderer:
      def __init__(self, state: RunState):
          self.state = state
          self.is_tty = sys.stdout.isatty()
          self.use_color = should_use_color()
      
      def update_display(self):
          if self.is_tty:
              # Use ANSI cursor positioning to keep status at bottom
              self._render_tty()
          else:
              # Just print raw output
              # Will print summary at the end
              pass
      
      def _render_tty(self):
          """Render with ANSI cursor positioning (TTY only)."""
          # Save cursor position
          # Move to bottom of screen
          # Clear lines
          # Print status
          # Restore cursor position
          pass
      
      def print_final_summary(self):
          """Print final summary (for both TTY and non-TTY)."""
          summary = self.render_host_summary()
          print(summary)
  ```

---

## Summary of nom-Style Compact View Research

| Question | Recommendation |
|----------|----------------|
| PQ1: nom layout | Fixed status at bottom (not full-screen TUI) |
| PQ2: Currently running | List with ⏵ icon, host, task, duration |
| PQ3: Per-host stats | Table with ✔/⚡/❌/⚠ columns, colored by worst status |
| PQ4: Textual single-panel | Use ANSI rendering for compact, Textual for full TUI |
| PQ5: Progress display | Show current play + running tasks + host summary |
| PQ6: Non-TTY behavior | Strip ANSI positioning, keep colors, print final summary |

## Implementation Plan

### Phase 1: Compact View (MVP)

1. **Create `CompactRenderer` class**:
   - ANSI-based rendering (Rich Console)
   - Fixed bottom status (cursor manipulation)
   - Per-host stats table
   - Currently running tasks list

2. **Create `RunState` class**:
   - Track plays, tasks, hosts
   - Aggregate stats per host
   - Calculate currently running tasks

3. **Main rendering loop**:
   ```python
   renderer = CompactRenderer(state)
   
   async for event in stream_ansible():
       state.handle_event(event)
       renderer.update_display()  # Updates bottom status
       sys.stdout.write(event.raw_line + "\n")  # Prints above status
       sys.stdout.flush()
   
   renderer.print_final_summary()
   ```

### Phase 2: Full TUI Mode

1. **Create `AOMApp` Textual app**:
   - TreePanel (play/task tree)
   - LogPanel (RichLog with streaming)
   - StatusBar (elapsed time, host count)

2. **Keyboard bindings**:
   - `q`: Quit
   - `↑/↓`: Navigate tree
   - `Enter`: Expand/collapse
   - `/`: Search
   - `Ctrl+C`: Copy selected line

3. **Integration**:
   ```python
   if args.tui:
       app = AOMApp()
       app.run()
   else:
       # Compact mode
       run_compact_mode()
   ```

---

*Research completed 2026-04-20*
---

## Terminal Rendering Research: nom-Style Fixed Bottom Status Panel (2026-04-20)

### Executive Summary

**Question**: How to implement a nom-style "fixed bottom status panel while logs scroll above" in Python?

**Finding**: nom uses **pure ANSI escape codes** with sophisticated cursor positioning to maintain a fixed status panel at the bottom of the terminal while logs scroll above it. This is NOT a full TUI - it's terminal manipulation.

**Key Technique**: nom calculates line counts, clears previous output, writes nix logs + padding + status panel, and uses DEC mode 2026 (synchronized output) to prevent flickering.

---

### DQ1: Can Rich Live do nom-style fixed bottom panel?

**Answer**: **YES, but with limitations**.

**Evidence from Rich Documentation**:

From `rich.live` docs:

```python
from rich.live import Live
from rich.table import Table

table = Table()
table.add_column("Row ID")
table.add_column("Description")
table.add_column("Level")

with Live(table, refresh_per_second=4) as live:
    # update 4 times a second to feel fluid
    for row in range(12):
        # THIS PRINTS ABOVE THE LIVE DISPLAY
        live.console.print(f"Working on row #{row}")
        time.sleep(0.4)
```

**Key Features**:

1. **`live.console.print()` prints above the live display** - This is exactly what we need for logs!
2. **`vertical_overflow='crop_above'`** - Shows bottom of content instead of top
3. **`screen=True`** - Use alternate screen buffer (like vim/top)
4. **Transient display** - Live display disappears when context exits

**Example for nom-style**:

```python
from rich.live import Live
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def render_status(state) -> Panel:
    """Render status panel."""
    grid = Table.grid()
    grid.add_column()
    grid.add_column(justify="right")
    
    grid.add_row("⏱", f"{state['elapsed']}")
    grid.add_row("Running:", f"Task {state['task_num']}/{state['total_tasks']}")
    grid.add_row("Hosts:", f"{state['hosts_done']}/{state['total_hosts']}")
    
    return Panel(grid, title="AOM Status", border_style="blue")

async def run_with_status():
    state = {"elapsed": "0:00", "task_num": 1, "total_tasks": 10, ...}
    
    with Live(render_status(state), refresh_per_second=4, screen=True) as live:
        async for line in stream_ansible_output():
            # Log output prints ABOVE live display
            live.console.print(line)
            
            # Update state
            state = update_state(state, line)
            live.update(render_status(state))
```

**Limitations**:

1. **Alternate screen buffer**: With `screen=True`, Rich uses the alternate buffer. When the app exits, logs disappear. Without `screen=True`, the live display might not stay at the bottom properly.

2. **Vertical overflow**: The `vertical_overflow='crop_above'` option (PR #3637) shows the bottom of content, which is closer to nom behavior but still requires careful management.

3. **Terminal resize**: Rich handles terminal resize automatically, but we need to recalculate status panel width.

**Verdict**: Rich Live can work for nom-style display, but for more control, use **blessed** or **ANSI codes directly**.

---

### DQ2: Can blessed/blessings create split-screen layout?

**Answer**: **YES**, blessed provides full cursor positioning API.

**Evidence from blessed Documentation**:

```python
from blessed import Terminal

term = Terminal()

# Context manager for cursor positioning
with term.location(0, term.height - 1):
    print('Here is the bottom.')

print('This is back where I came from.')
```

**Key Features**:

1. **`term.location(x, y)`** - Context manager for temporary cursor positioning
2. **`term.move_xy(x, y)`** - Move cursor to absolute position
3. **`term.height` / `term.width`** - Terminal dimensions
4. **`term.clear_eol` / `term.clear_eos`** - Clear to end of line / screen
5. **`term.save` / `term.restore`** - Save/restore cursor (via context manager)
6. **SIGWINCH support** - `term.notify_on_resize()` for terminal resize handling

**Example for nom-style**:

```python
from blessed import Terminal
import sys

term = Terminal()

lines_printed = 0
status_height = 5

def clear_status():
    """Clear the status panel area."""
    # Move to bottom of screen, clear lines
    for i in range(status_height):
        sys.stdout.write(term.move_xy(0, term.height - status_height + i))
        sys.stdout.write(term.clear_eol)
    sys.stdout.flush()

def render_status(state):
    """Render status panel at bottom."""
    clear_status()
    
    # Render status lines
    lines = [
        f"⏱ {state['elapsed']}",
        f"Task {state['task']}/{state['total']}",
        f"Hosts: {state['hosts_done']}/{state['total_hosts']}",
        "",
        "Web1: ✔5 ⚡2 ❌0 | DB1: ✔3 ❌1"
    ]
    
    for i, line in enumerate(lines[-status_height:]):
        sys.stdout.write(term.move_xy(0, term.height - status_height + i))
        sys.stdout.write(line)
    
    sys.stdout.flush()

def handle_resize(sig, action):
    """Handle terminal resize."""
    render_status(state)

# Set up resize handler
import signal
signal.signal(signal.SIGWINCH, handle_resize)

async def run_with_status():
    with term.fullscreen(), term.hidden_cursor():
        for line in stream_ansible():
            # Print log line (scrolled)
            print(line)
            lines_printed += 1
            
            # Update status at bottom
            render_status(state)
```

**Verdict**: blessed is **excellent** for nom-style rendering. Provides low-level control, proper cursor positioning, and terminal detection.

---

### DQ3: Can curtsies create split-screen layout?

**Answer**: **YES**, but it's less documented than blessed.

**Evidence from curtsies Documentation**:

curtsies provides:
- `FullscreenWindow` - Alternate screen buffer (like vim)
- `CursorAwareWindow` - Normal screen with cursor tracking
- `FSArray` - 2D grid of formatted text

**Example**:

```python
from curtsies import FullscreenWindow, fsarray
import time

with FullscreenWindow() as win:
    for i in range(10):
        arr = fsarray([
            "Log line " + str(i),
            "",
            "Status: Running"
        ])
        win.render_to_terminal(arr)
        time.sleep(0.5)
```

**Verdict**: curtsies works, but blessed has better documentation and is more widely used.

---

### DQ4: Can we use ANSI escape codes directly?

**Answer**: **YES**, and this is how nom (Haskell) does it!

**Evidence from nom Source Code** (`lib/NOM/IO.hs` lines 128-170):

```haskell
-- Key ANSI codes used by nom:
startAtomicUpdate = "\x1b[?2026h"  -- DEC mode 2026: synchronized updates
endAtomicUpdate = "\x1b[?2026l"

-- Cursor positioning
Terminal.setCursorColumnCode 0      -- Move cursor to start of line
Terminal.cursorUpLineCode 1         -- Move cursor up 1 line
Terminal.clearLineCode               -- Clear current line

-- Rendering logic:
-- 1. Start atomic update (prevents flicker)
-- 2. Clear previous output:
--    - Clear current line (if last_printed_line_count > 0)
--    - Move up and clear (for each previously printed line)
-- 3. Print nix output + padding + nom status
-- 4. End atomic update
```

**nom's Algorithm** (from lines 100-195):

1. **Track line count**: `printed_lines_var` tracks how many lines were written
2. **Calculate padding**: `lines_to_pad` = max(0, last_printed_line_count - nix_output_length - nom_output_length)
3. **Clear previous output**:
   - Clear current line
   - Move up and clear for each previous line
4. **Print new output**:
   - Nix logs (with newlines for scrolling)
   - Padding lines (to prevent status from jumping up)
   - Nom status panel
5. **Use synchronized output** (DEC mode 2026) to prevent flickering

**ANSI Codes Reference**:

```python
# Save/Restore cursor
ESC_7 = "\0337"   # Save cursor (DEC)
ESC_8 = "\0338"   # Restore cursor (DEC)
CSI_s = "\033[s"  # Save cursor (SCO)
CSI_u = "\033[u"  # Restore cursor (SCO)

# Cursor movement
CSI_nA = "\033[{n}A"      # Move cursor up n lines
CSI_nB = "\033[{n}B"      # Move cursor down n lines
CSI_n_Col_H = "\033[{row};{col}H"  # Move cursor to absolute position

# Clearing
CSI_K = "\033[K"   # Clear from cursor to end of line
CSI_0K = "\033[0K"  # Clear from cursor to end of line (same as K)
CSI_1K = "\033[1K"  # Clear from start of line to cursor
CSI_2K = "\033[2K"  # Clear entire line
CSI_0J = "\033[0J"  # Clear from cursor to end of screen
CSI_1J = "\033[1J"  # Clear from start to cursor
CSI_2J = "\033[2J"  # Clear entire screen

# Synchronized output (DEC mode 2026)
DEC_2026h = "\033[?2026h"  # Begin synchronized output
DEC_2026l = "\033[?2026l"  # End synchronized output

# Alternate screen buffer
DEC_1049h = "\033[?1049h"  # Enable alternate buffer
DEC_1049l = "\033[?1049l"  -- Disable alternate buffer

# Cursor visibility
DEC_25l = "\033[?25l"  # Hide cursor
DEC_25h = "\033[?25h"  # Show cursor
```

**Python Implementation**:

```python
import sys

class ANSI:
    """ANSI escape codes."""
    
    # Cursor movement
    UP = "\033[{n}A"
    DOWN = "\033[{n}B"
    MOVE_TO = "\033[{row};{col}H"
    
    # Clearing
    CLEAR_LINE = "\033[2K"
    CLEAR_REST_OF_LINE = "\033[K"
    CLEAR_REST_OF_SCREEN = "\033[0J"
    
    # Save/Restore cursor
    SAVE = "\033[s"
    RESTORE = "\033[u"
    
    # Synchronized output
    BEGIN_SYNC = "\033[?2026h"
    END_SYNC = "\033[?2026l"
    
    # Alternate buffer
    BEGIN_ALT = "\033[?1049h"
    END_ALT = "\033[?1049l"
    
    # Cursor visibility
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"


class CompactRenderer:
    """nom-style compact status renderer using ANSI codes."""
    
    def __init__(self, state):
        self.state = state
        self.lines_printed = 0
        self.status_height = 5
        self.terminal_height = self.get_terminal_height()
        self.terminal_width = self.get_terminal_width()
    
    def get_terminal_height(self):
        import os
        try:
            return os.get_terminal_size().lines
        except:
            return 24
    
    def get_terminal_width(self):
        import os
        try:
            return os.get_terminal_size().columns
        except:
            return 80
    
    def clear_previous_status(self):
        """Clear lines used by previous status."""
        # Move to bottom of screen
        sys.stdout.write(ANSI.MOVE_TO.format(
            row=self.terminal_height - self.status_height,
            col=0
        ))
        
        # Clear each status line
        for _ in range(self.status_height):
            sys.stdout.write(ANSI.CLEAR_LINE)
            sys.stdout.write(ANSI.DOWN.format(n=1))
    
    def render_status(self):
        """Render status panel at bottom."""
        lines = [
            f"⏱ {self.state.elapsed}",
            f"Task {self.state.task_num}/{self.state.total_tasks}",
            f"Hosts: {self.state.hosts_done}/{self.state.total_hosts}",
            "",
            "| Web1: ✔5 ⚡2 | DB1: ✔3 ❌1 |"
        ]
        
        # Use synchronized output to prevent flicker
        sys.stdout.write(ANSI.BEGIN_SYNC)
        
        # Clear previous status
        self.clear_previous_status()
        
        # Move to bottom
        sys.stdout.write(ANSI.MOVE_TO.format(
            row=self.terminal_height - self.status_height + 1,
            col=0
        ))
        
        # Write status lines
        for line in lines:
            sys.stdout.write(line + "\n")
        
        sys.stdout.write(ANSI.END_SYNC)
        sys.stdout.flush()
    
    def print_log_line(self, line):
        """Print a log line (scrolling above status)."""
        # Move cursor to just above status
        # Print the line (it scrolls up)
        # Then restore status
        
        # In practice, we just print the line
        # The status will be re-rendered after
        print(line)
        self.render_status()
```

**Verdict**: Using ANSI codes directly gives **maximum control** and is how nom works. This is the best approach for a nom-style compact view.

---

### DQ5: Can urwid create this layout?

**Answer**: **YES**, but urwid is a full TUI framework (heavier than needed).

**Evidence from urwid Documentation**:

urwid provides:
- `ListBox` - Scrollable content
- `Pile` - Vertical stack of widgets
- `Frame` - Header + body + footer layout
- `Overlay` - Overlay one widget on another

**Example**:

```python
import urwid

# Scrollable log content
logs = urwid.SimpleFocusListWalker([
    urwid.Text("Log line 1"),
    urwid.Text("Log line 2"),
])
log_box = urwid.ListBox(logs)

# Fixed status panel at bottom
status_text = urwid.Text("Status: Running")
status_panel = urwid.LineBox(status_text, title="AOM Status")

# Layout: logs above, status below
layout = urwid.Frame(
    body=log_box,
    footer=status_panel
)

# Run TUI
def main():
    urwid.MainLoop(layout).run()
```

**Verdict**: urwid CAN work, but it's overkill for compact mode. Use it for the full TUI mode, but use ANSI/blessed for compact mode.

---

### DQ6: Can Textual run in minimal "streaming" mode?

**Answer**: Textual has **inline mode**, but it's still a TUI framework.

**Evidence from Textual Blog** (April 2024):

```python
from textual.app import App, ComposeResult
from textual.widgets import TextArea

class InlineApp(App):
    CSS = """
    TextArea {
        height: auto;
        max-height: 50vh;
    }
    """

    def compose(self) -> ComposeResult:
        yield TextArea(language="python")

if __name__ == "__main__":
    InlineApp().run(inline=True)
```

**How Textual Inline Works**:

From the blog post:
1. Textual renders the app at the current cursor position
2. Uses cursor manipulation to place app inline
3. App can grow/shrink in height
4. Mouse and keyboard input work correctly
5. Uses escape codes to query cursor position

**Key Insight**: Textual calculates the cursor position, renders the app, and positions text entry widgets correctly.

**Verdict**: Textual inline mode is **NOT** suitable for nom-style compact mode because:
- It's still a full TUI framework (with lifecycle, event loop, etc.)
- We need lightweight ANSI-only rendering for compact mode
- Use Textual for full TUI mode (with `--tui` flag)

---

### DQ7: Can Rich + ANSI combination work?

**Answer**: **YES**, combine Rich for formatting + ANSI for positioning.

**Best of Both Worlds**:

```python
from rich.console import Console
from rich.text import Text
from rich.table import Table
import sys

console = Console()

class HybridRenderer:
    """Use Rich for formatting, ANSI for positioning."""
    
    def __init__(self):
        self.status_height = 7
        self.lines_printed = 0
        
        # Get terminal size
        import os
        try:
            self.height = os.get_terminal_size().lines
            self.width = os.get_terminal_size().columns
        except:
            self.height = 24
            self.width = 80
    
    def format_status(self, state) -> str:
        """Use Rich to format status panel."""
        table = Table(show_header=False, box=None)
        table.add_column("", style="cyan")
        table.add_column(justify="right")
        
        table.add_row("⏱", state['elapsed'])
        table.add_row("Running:", f"Task {state['task']}/{state['total']}")
        
        # Rich renders to string
        with console.capture() as capture:
            console.print(table)
        
        return capture.get()
    
    def render_at_bottom(self, content: str):
        """Render content at bottom using ANSI."""
        # Move cursor to bottom - status_height
        sys.stdout.write(f"\033[{self.height - self.status_height};0H")
        
        # Clear the area
        for i in range(self.status_height):
            sys.stdout.write("\033[K")  # Clear line
            if i < self.status_height - 1:
                sys.stdout.write("\033[B")  # Move down
        
        # Move back up
        sys.stdout.write(f"\033[{self.status_height - 1}A")
        
        # Write content
        sys.stdout.write(content)
        sys.stdout.flush()
    
    def print_log(self, line: str):
        """Print log line (scrolled)."""
        # Just print it (scrolls up naturally)
        print(line)
        
        # Re-render status at bottom
        self.render_at_bottom(self.format_status(state))
```

**Verdict**: This approach works well - Rich for beautiful formatting, ANSI codes for positioning.

---

### DQ8: How to handle terminal resize (SIGWINCH)?

**Answer**: Use **blessed's resize handling** or install a **SIGWINCH handler**.

**Evidence from blessed Documentation**:

```python
from blessed import Terminal
import signal
import threading

term = Terminal()
resize_pending = threading.Event()

def on_resize(*args):
    """Signal handler sets a flag."""
    resize_pending.set()

# Install handler (Unix only)
signal.signal(signal.SIGWINCH, on_resize)

# Alternative: blessed's in-band resize
with term.notify_on_resize():
    # When terminal resizes, inkey(timeout) will return None
    # Check term.height and term.width
    pass
```

**Python Implementation**:

```python
import signal
import os
import threading

class ResizeHandler:
    """Handle terminal resize."""
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.resize_event = threading.Event()
    
    def setup(self):
        """Install resize handler."""
        if hasattr(signal, 'SIGWINCH'):
            signal.signal(signal.SIGWINCH, self._on_resize)
    
    def _on_resize(self, signum, frame):
        """Called on SIGWINCH."""
        # Just set flag - don't do complex work in signal handler
        self.resize_event.set()
    
    def check_and_handle(self):
        """Check if resize happened and handle it."""
        if self.resize_event.is_set():
            self.resize_event.clear()
            # Get new dimensions
            try:
                self.renderer.height = os.get_terminal_size().lines
                self.renderer.width = os.get_terminal_size().columns
            except:
                pass
            
            # Re-render status
            self.renderer.render_status()
```

**Alternative: blessed notify_on_resize**:

```python
from blessed import Terminal

term = Terminal()

with term.notify_on_resize():
    # term.inkey() will return None on resize
    while True:
        key = term.inkey(timeout=0.1)
        if key is None:
            # Check if it's a resize
            if term.height != old_height or term.width != old_width:
                old_height = term.height
                old_width = term.width
                render_status()
```

**Verdict**: Use blessed's resize handling for cross-platform support, or SIGWINCH directly on Unix.

---

### DQ9: How to handle password prompts?

**Answer**: **Pause status rendering, let ansible handle prompt inline**.

**Problem**: When using fixed-bottom status, a password prompt needs to appear at the cursor position (not at the bottom).

**Solution from nom**:

nom just lets the program (nix) handle prompts. The status panel will be overwritten by the prompt.

**Implementation**:

```python
import sys
import getpass

class CompactRenderer:
    def __init__(self):
        self.status_active = False
        self.saved_cursor_pos = None
    
    def pause_status(self):
        """Pause status rendering for password prompt."""
        self.status_active = False
        # Clear status from bottom
        self.clear_status()
    
    def resume_status(self):
        """Resume status rendering after prompt."""
        self.status_active = True
        self.render_status()
    
    def handle_password_prompt(self, prompt: str) -> str:
        """Handle password input."""
        # Pause status rendering
        self.pause_status()
        
        # Get password (appears inline)
        password = getpass.getpass(prompt)
        
        # Resume status
        self.resume_status()
        
        return password

# Usage with ansible
async def stream_ansible_with_prompts():
    renderer = CompactRenderer()
    
    async for event in stream_ansible():
        if event.type == "password_prompt":
            # Handle password
            password = renderer.handle_password_prompt(event.prompt)
            # Send password back to ansible
            await send_password(password)
        else:
            # Normal log line
            print(event.line)
            renderer.render_status()
```

**Alternative: Full-screen TUI for prompts**:

If using Textual for full mode:
- Textual handles password input via `Input(password=True)`
- Modal will appear within the TUI

**Verdict**: Pause status panel, let ansible's password prompt appear inline. Resume status after.

---

### DQ10: How to gracefully handle crashes?

**Answer**: **Exception wrapper with cleanup**.

**Implementation**:

```python
import sys
import traceback

class AnsibleRunner:
    def __init__(self, playbook: str):
        self.playbook = playbook
        self.renderer = CompactRenderer()
        self.state = RunState()
    
    def cleanup(self):
        """Clean up terminal state on exit."""
        # Show cursor
        sys.stdout.write("\033[?25h")
        
        # Exit alternate buffer (if used)
        if hasattr(self.renderer, 'alternate_buffer') and self.renderer.alternate_buffer:
            sys.stdout.write("\033[?1049l")
        
        # Flush
        sys.stdout.flush()
    
    def run(self):
        """Run ansible-playbook with error handling."""
        try:
            return self._run_playbook()
        
        except KeyboardInterrupt:
            print("\n[Interrupted by user]")
            return 130  # Standard exit code for SIGINT
        
        except Exception as e:
            # Show error
            print(f"\n[AOM Error] {e}\n")
            traceback.print_exc()
            return 1
        
        finally:
            # ALWAYS clean up terminal
            self.cleanup()
    
    def _run_playbook(self):
        """Actually run the playbook."""
        # Stream ansible-playbook output
        # Update state
        # Render status
        pass

# Usage
if __name__ == "__main__":
    runner = AnsibleRunner(sys.argv[1])
    sys.exit(runner.run())
```

**Graceful Degradation**:

```python
class CompactRenderer:
    def __init__(self, state: RunState):
        self.state = state
        self.tty = sys.stdout.isatty()
        self.use_color = self._should_use_color()
    
    def _should_use_color(self) -> bool:
        """Check if we should use ANSI colors."""
        import os
        
        # Force color
        if os.environ.get('FORCE_COLOR'):
            return True
        
        # No color
        if os.environ.get('NO_COLOR'):
            return False
        
        # Check TTY
        return self.tty
    
    def render(self):
        """Render status panel."""
        # Build status lines
        lines = [
            f"⏱ {self.state.elapsed}",
            f"Task {self.state.task}/{self.state.total}",
            f"Hosts: {self.state.hosts_done}/{self.state.total_hosts}"
        ]
        
        # Add color if enabled
        if self.use_color:
            lines = [self._colorize(line) for line in lines]
        
        # Return string
        return "\n".join(lines)
    
    def update_display(self):
        """Update terminal display."""
        if not self.tty:
            # Non-TTY: just print summary periodically
            if self.state.should_print_summary():
                print(self.render())
            return
        
        # TTY: use ANSI positioning
        self._update_display_tty()
    
    def print_final_summary(self):
        """Print final summary (for both TTY and non-TTY)."""
        print("\nPLAY RECAP " + "=" * 70)
        print(self.render_host_summary())
```

**Verdict**: Always clean up terminal state, check for TTY, degrade gracefully.

---

### DQ11: What about non-TTY fallback?

**Answer**: **Print logs normally, show summary at end**.

**Evidence**: When stdout is not a TTY (piped to file, grep, etc.), ANSI cursor codes will be printed literally, which is not useful.

**Implementation**:

```python
class CompactRenderer:
    def __init__(self, state: RunState):
        self.state = state
        self.is_tty = sys.stdout.isatty()
    
    def update_display(self):
        """Update display (TTY-aware)."""
        if self.is_tty:
            # Use ANSI positioning for fixed bottom
            self._render_tty()
        # else: Don't do live updates
    
    def _render_tty(self):
        """Render with ANSI positioning."""
        # ... (ANSI manipulation)
        pass
    
    # Called after ansible-playbook finishes
    def print_final_summary(self):
        """Print final summary."""
        print("\n" + "=" * 70)
        print("PLAY RECAP")
        print("=" * 70)
        
        for host, stats in self.state.host_stats.items():
            ok = stats.get('ok', 0)
            changed = stats.get('changed', 0)
            failed = stats.get('failed', 0)
            unreachable = stats.get('unreachable', 0)
            
            print(f"{host} : ok={ok} changed={changed} failed={failed} unreachable={unreachable}")
```

**Usage**:

```bash
# TTY (interactive)
$ aom site.yml
[logs scroll]
┏━━ AOM Status ━━━━┓
┃ ⏱ 2:34           ┃
┃ Task 8/10        ┃
┗━━━━━━━━━━━━━━━━━━┛

# Non-TTY (piped)
$ aom site.yml | grep ERROR
ERROR: Task failed on web2
ERROR: Host unreachable: db1

PLAY RECAP
==========
web1 : ok=5 changed=2 failed=0
web2 : ok=3 changed=0 failed=1
db1 : ok=0 changed=0 unreachable=1
```

**Verdict**: TTY = live status panel; Non-TTY = normal log output + final summary.

---

## Summary: Recommended Architecture

### For Compact Mode (nom-style)

**Best approach**: **blessed + ANSI** or **Rich + ANSI hybrid**.

**Why**:
1. **blessed** provides terminal detection, cursor positioning, resize handling
2. **ANSI codes** give fine-grained control (how nom works)
3. **Rich** can format tables/panels nicely
4. **No TUI framework overhead** - just terminal manipulation

**Implementation Plan**:

```python
# aom/renderer_compact.py

from blessed import Terminal
from rich.console import Console
from rich.table import Table
import sys
import signal
import threading

class CompactRenderer:
    """nom-style compact status renderer."""
    
    def __init__(self, state: RunState):
        self.state = state
        self.term = Terminal()
        self.console = Console()
        
        # Terminal state
        self.is_tty = sys.stdout.isatty()
        self.use_color = self._should_use_color()
        
        # Track what we've printed
        self.lines_printed = 0
        self.status_height = 7
        
        # Setup resize handler
        self.resize_event = threading.Event()
        if hasattr(signal, 'SIGWINCH'):
            signal.signal(signal.SIGWINCH, self._on_resize)
    
    def _on_resize(self, signum, frame):
        """Handle terminal resize."""
        self.resize_event.set()
    
    def check_resize(self):
        """Check and handle resize."""
        if self.resize_event.is_set():
            self.resize_event.clear()
            self.render_status()
    
    def render_status_rich(self) -> str:
        """Render status as Rich table."""
        table = Table(show_header=False, box=None, padding=0)
        table.add_column("", style="cyan", width=1)
        table.add_column(justify="right")
        
        # Time
        elapsed = self.state.elapsed_time
        table.add_row("⏱", elapsed)
        
        # Current task
        current = self.state.current_task
        if current:
            table.add_row("⏵", f"{current.host}: {current.name} ({current.duration})")
        
        # Host stats
        table.add_row("", "")
        table.add_row("Stats", f"{self.state.hosts_done}/{self.state.total_hosts} hosts")
        
        with self.console.capture() as capture:
            self.console.print(table)
        
        return capture.get()
    
    def clear_status_ansi(self):
        """Clear status area using ANSI."""
        # Move to bottom - status_height
        row = self.term.height - self.status_height
        sys.stdout.write(f"\033[{row};0H")
        
        # Clear status_height lines
        for _ in range(self.status_height):
            sys.stdout.write("\033[K")  # Clear line
            sys.stdout.write("\033[B")  # Move down
        
        sys.stdout.flush()
    
    def render_status(self):
        """Render status panel at bottom."""
        if not self.is_tty:
            return  # No live updates for non-TTY
        
        # Clear previous status
        self.clear_status_ansi()
        
        # Render status content
        content = self.render_status_rich()
        
        # Move to bottom
        row = self.term.height - self.status_height + 1
        sys.stdout.write(f"\033[{row};0H")
        
        # Write content
        sys.stdout.write(content)
        sys.stdout.flush()
    
    def print_log_line(self, line: str):
        """Print a log line (scrolled above status)."""
        print(line)  # Normal print (scrolls up)
        self.lines_printed += 1
        
        # Re-render status at bottom
        self.render_status()
    
    def handle_password_prompt(self, prompt: str) -> str:
        """Handle password input."""
        import getpass
        
        # Pause status
        self.clear_status_ansi()
        self.status_active = False
        
        # Get password
        password = getpass.getpass(prompt)
        
        # Resume status
        self.status_active = True
        self.render_status()
        
        return password
    
    def cleanup(self):
        """Clean up terminal state."""
        if self.is_tty:
            # Show cursor
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
    
    def print_final_summary(self):
        """Print final summary."""
        print("\n" + "=" * 70)
        print("PLAY RECAP")
        print("=" * 70)
        # ... (print host stats)
```

### For Full TUI Mode

**Best approach**: **Textual App with panels**.

```python
# aom/renderer_tui.py

from textual.app import App, ComposeResult
from textual.widgets import Tree, RichLog, Footer, Header
from textual.containers import Container

class AOMApp(App):
    """Full TUI for AOM."""
    
    CSS = """
    Tree {
        width: 1fr;
    }
    RichLog {
        width: 1fr;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Tree("Plays", id="tree")
            yield RichLog(id="log")
        yield Footer()
    
    def on_mount(self):
        # Start streaming ansible output
        pass
    
    def update_state(self, state: RunState):
        """Update TUI with new state."""
        # Update tree
        # Update log
        pass

# Usage
if args.tui:
    app = AOMApp()
    app.run()
else:
    # Compact mode
    run_compact_mode()
```

---

## Final Recommendations

| Feature | Compact Mode | Full TUI Mode |
|---------|--------------|---------------|
| **Library** | blessed + ANSI (or Rich Console) | Textual |
| **Rendering** | Manual ANSI cursor positioning | Textual widgets |
| **Layout** | Fixed bottom status | Full screen panels |
| **Interaction** | None (just logs) | Keyboard navigation |
| **Password prompt** | Pause + getpass | Textual Input widget |
| **Crash handling** | try/except + cleanup | Textual exception handling |
| **Non-TTY** | Logs + final summary | Error (requires TTY) |
| **Resize** | SIGWINCH handler | Textual handles |
| **Example** | nom, apt-get | htop, lazydocker |

**Implementation Steps**:

1. **Phase 1: Compact Mode** (Priority)
   - Create `CompactRenderer` class using blessed/ANSI
   - Implement status rendering with Rich formatting
   - Handle TTY detection and non-TTY fallback
   - Add password prompt support
   - Add SIGWINCH handler

2. **Phase 2: Full TUI Mode**
   - Create `AOMApp` Textual app
   - Implement tree view, log panel, status bar
   - Add keyboard navigation
   - Integrate with same `RunState` as compact mode

3. **Phase 3: Polish**
   - Add color themes
   - Add progress bars for long tasks
   - Add search in TUI mode
   - Add export summary feature

---

*Research completed 2026-04-20*

---

## ANSIBLE PASSWORD PROMPT HANDLING IN COMPACT/ANSI MODE (2026-04-20)

### OVERVIEW

**Context**: When running `ansible-playbook` in compact/ANSI mode (NOT Textual), with pexpect handling the subprocess through a PTY, we need to handle password prompts (vault passwords, become passwords, SSH passwords). These prompts require user input but our status renderer controls the terminal.

**Key Challenge**: How to pause the ANSI rendering, let the user interact with the password prompt (masked input), then resume rendering — ALL without Textual.

---

### PQ7: How does getpass.getpass() work with pexpect PTY?

**Context**: When ansible-playbook is run in a pexpect PTY, it uses getpass.getpass() which reads from /dev/tty. Can the user simply type the password at the terminal?

**Answer**: **YES, but it's not automatic.**

**How getpass works** (from Python 3.13+ `Lib/getpass.py`):

```python
def unix_getpass(prompt='Password: ', stream=None, *, echo_char=None):
    """Prompt for a password, with echo turned off."""
    try:
        # Always try reading and writing directly on the tty first.
        fd = os.open('/dev/tty', os.O_RDWR|os.O_NOCTTY)
        tty = io.FileIO(fd, 'w+')
        input = io.TextIOWrapper(tty)
        # ... set up terminal, disable echo, read password
    except OSError:
        # Fallback to stdin if no tty
        passwd = fallback_getpass(prompt, stream)
```

**Key Points**:

1. **getpass opens /dev/tty directly** - NOT stdin/stderr
2. **In a PTY, /dev/tty refers to the slave side** - When pexpect.spawn() creates a PTY, the subprocess's /dev/tty is the PTY slave
3. **The pexpect process controls the PTY master** - It can choose to forward data or not

**Evidence from Python source** ([cpython/Lib/getpass.py lines 70-130](https://github.com/python/cpython/blob/main/Lib/getpass.py#L70-L130)):

```python
# getpass tries to open /dev/tty
fd = os.open('/dev/tty', os.O_RDWR|os.O_NOCTTY)

# Disables terminal ECHO
new[3] &= ~termios.ECHO  # lflags

# If echo_char specified, also disables ICANON and IEXTEN
if echo_char:
    new[3] &= ~termios.ICANON   # non-canonical mode  
    new[3] &= ~termios.IEXTEN   # disable literal next handling
```

**The Problem**:

When we use Rich's Live display to render status at the bottom of the screen, we're controlling the terminal. The getpass prompt from ansible-playbook would go to the PTY slave, and pexpect would see it on the PTY master. **But the ACTUAL terminal is still available** for user input IF we:

1. Stop our rendering (free up the terminal)
2. Pass the prompt through to the actual terminal
3. Let the user type (getpass handles masking)
4. Resume rendering

**Evidence from Stack Overflow** (pexpect password detection):

> "The `waitnoecho()` method waits until the terminal ECHO flag is set False. This returns True if the echo mode is off. This can be used to detect when the child is waiting for a password."
> — [pexpect documentation](https://pexpect.readthedocs.io/en/stable/api/pexpect.html#pexpect.spawn.waitnoecho)

**Implementation Pattern**:

```python
# pexpect's waitnoecho() detects password prompts
p = pexpect.spawn('ssh user@example.com')
p.waitnoecho()  # Wait until child disables echo (password prompt)
p.sendline(mypassword)
```

**For ansible-playbook in our PTY**:

```python
import pexpect

child = pexpect.spawn('ansible-playbook site.yml')

# Pattern 1: Detect password prompt by output
child.expect(['Vault password:', 'BECOME password:', 'SSH password:'])

# Pattern 2: Detect by terminal ECHO flag
if child.waitnoecho(timeout=0.5):  # Non-blocking check
    # Password prompt detected (subprocess disabled echo)
    # Stop our rendering, pass through to terminal
    ...
```

---

### PQ8: How to pause and resume Rich Live rendering for password prompts?

**Context**: Rich's `Live` display controls the terminal with ANSI cursor positioning. We need to stop it, let the user interact with a password prompt, then restart it.

**Answer**: Use `Live.stop()` and `Live.start()` methods.

**Rich Live API** (from Rich documentation):

```python
from rich.live import Live
from rich.console import Console

console = Console()

with Live(console=console) as live:
    # Rendering happens here
    live.update(renderable)
    
    # To pause:
    live.stop()  # Stops rendering, frees terminal
    
    # ... user interacts with terminal ...
    
    # To resume:
    live.start()  # Resumes rendering
```

**Evidence from Rich source** ([rich/live.py](https://github.com/Textualize/rich/blob/master/rich/live.py)):

```python
def start(self, refresh: bool = False) -> None:
    """Start live rendering display."""
    with self._lock:
        if self._started:
            return
        self._started = True
        # ... setup rendering thread, redirect stdout/stderr ...

def stop(self) -> None:
    """Stop live rendering display."""
    with self._lock:
        if not self._started:
            return
        self._started = False
        self.console.clear_live()
        # ... stop rendering thread, restore stdout/stderr ...
```

**Key Points**:

1. **`stop()` clears the live display** - Removes the status widget from screen
2. **`stop()` restores stdout/stderr** - Returns control to normal terminal
3. **`start()` reinitializes display** - Restores the status widget
4. **Thread-safe** - Uses lock to prevent race conditions

**Important**: When Live is started, it redirects `sys.stdout` and `sys.stderr` by default. This is why stopping Live frees the terminal for interaction.

**From Rich docs**:

> "The Live class will create an internal Console object... To avoid breaking the live display visuals, Rich will redirect `stdout` and `stderr`..."
> — [Live Display documentation](https://rich.readthedocs.io/en/stable/live.html#redirecting-stdout-stderr)

**Implementation Pattern**:

```python
from rich.live import Live
from rich.console import Console
from rich.panel import Panel
import pexpect

class CompactRunner:
    def __init__(self):
        self.console = Console()
        self.live = Live(console=self.console, refresh_per_second=10)
        self.child = None
    
    def run_ansible(self, playbook: str):
        """Run ansible-playbook with compact status display."""
        self.live.start()
        
        try:
            self.child = pexpect.spawn(f'ansible-playbook {playbook}')
            self.child.logfile_read = sys.stdout  # Pass through output
            
            while True:
                # Check for password prompts
                i = self.child.expect([
                    'Vault password:',
                    'BECOME password:',
                    'SSH password:', 
                    pexpect.EOF,
                    pexpect.TIMEOUT
                ], timeout=None)
                
                if i < 3:  # Password prompt detected
                    self._handle_password_prompt()
                elif i == 3:  # EOF
                    break
                else:  # TIMEOUT (shouldn't happen with timeout=None)
                    continue
                    
        finally:
            self.live.stop()
    
    def _handle_password_prompt(self):
        """Handle password prompt by stopping Live, letting user input."""
        # Stop rendering (frees terminal)
        self.live.stop()
        
        try:
            # The prompt is already in pexpect's buffer
            # Display it to user
            prompt = self.child.before.decode('utf-8')
            self.console.print(prompt, end='')
            
            # Get password from user (masked)
            # getpass will read from /dev/tty (actual terminal)
            import getpass
            password = getpass.getpass('')
            
            # Send password to ansible-playbook
            self.child.sendline(password)
            
        finally:
            # Resume rendering
            self.live.start()
```

---

### PQ9: Can we just let pexpect's default behavior handle password prompts in compact mode?

**Context**: When in compact mode, can we let pexpect's default behavior handle password prompts without special handling?

**Answer**: **NO - we need explicit handling.**

**Why pexpect alone is insufficient**:

1. **pexpect doesn't forward prompts to user by default**:
   - The prompt is captured in `child.before`
   - pexpect just matches patterns, doesn't automatically show them
   
2. **pexpect doesn't get user input automatically**:
   - You must explicitly call `sendline()` to send data
   - pexpect doesn't read from stdin to forward to child

**Evidence from pexpect documentation**:

```python
# Typical pexpect password handling pattern
child = pexpect.spawn('ssh user@example.com')
child.expect('password:')           # Just pattern matching
password = getpass.getpass('Password: ')  # You must get input yourself
child.sendline(password)            # You must send it explicitly
```

**From Stack Overflow** ([How do I collect ALL output from pexpect.spawn()?](https://stackoverflow.com/questions/67238593)):

> "pexpect gets everything the terminal shows, including commands and outputs. **Fortunate, passwords are not shown** (emphasis added), so unfortunately pexpect can't see them."
> 
> "To get the password from user, use getpass: `password = getpass.getpass()`"

**The issue**: If we don't handle password prompts explicitly, the user will never see them (captured in pexpect buffer) and won't be able to respond (no input mechanism).

**What we need to do**:

```python
while True:
    i = child.expect([
        'Vault password:',
        'BECOME password:',
        'SSH password:',
        'password:',
        pexpect.EOF
    ])
    
    if i < 4:  # Password prompt
        # STOP rendering
        live.stop()
        
        # SHOW prompt to user
        print(child.before.decode('utf-8'), end='')
        
        # GET password from user
        password = getpass.getpass('')
        
        # SEND to child
        child.sendline(password)
        
        # RESUME rendering
        live.start()
    else:
        # EOF - ansible finished
        break
```

---

### PQ10: How does Rich Live stop/start work with terminal state?

**Context**: We need to understand the terminal state changes when stopping/starting Live to ensure password prompts work correctly.

**Answer**: Rich Live manages terminal state carefully, but we need to be aware of stdout/stderr redirection.

**What happens when Live stops**:

From Rich source code analysis:

```python
def stop(self) -> None:
    """Stop live rendering display."""
    with self._lock:
        if not self._started:
            return
        self._started = False
        self.console.clear_live()
        
        if self.auto_refresh and self._refresh_thread is not None:
            self._refresh_thread.stop()
            self._refresh_thread = None
        
        # Important: Disables stdout/stderr redirection
        self._disable_redirect_io()
```

**Key terminal state changes**:

1. **`console.clear_live()`**: Clears the live display area, restores cursor position
2. **`_disable_redirect_io()`**: Restores original `sys.stdout` and `sys.stderr`
3. **Stops refresh thread**: No more background writes to terminal

**After `stop()`, the terminal is in "normal mode"**:
- stdout/stderr point to original streams (not internal buffers)
- Cursor is at the last line of the live display
- ANSI rendering is disabled

**When `start()` is called**:

1. **`_enable_redirect_io()`**: Redirects stdout/stderr to internal buffers
2. **Starts refresh thread**: Begins rendering loop
3. **Sets `self._started = True`**: Marks Live as active

**Important consideration**:

When Live is running, it redirects stdout/stderr. This means:

```python
# This prints to Live's internal buffer (not visible)
print("This goes to live buffer")

# To print DURING Live, use Live's console:
live.console.print("This prints above live display")
```

**For password handling**:

```python
def _handle_password_prompt(self):
    # Stop Live (frees terminal, restores stdin/stdout/stderr)
    self.live.stop()
    
    # sys.stdout now points to ACTUAL terminal
    # sys.stdin now points to ACTUAL terminal
    
    # Clear any buffered output from pexpect
    sys.stdout.flush()
    
    # Print prompt (via actual stdout)
    sys.stdout.write(self.child.before.decode('utf-8'))
    sys.stdout.flush()
    
    # Read password (via actual stdin, masked by getpass)
    # getpass.getpass() opens /dev/tty directly
    password = getpass.getpass('')
    
    # Send to ansible
    self.child.sendline(password)
    
    # Resume Live
    self.live.start()
```

**Terminal mode during password input**:

The terminal is in whatever mode it was before Live started. getpass handles the terminal mode switching for password input:

```python
# getpass temporarily:
# 1. Disables echo
# 2. (optionally) disables canonical mode (ICANON)
# 3. Reads raw input
# 4. Restores original terminal settings
```

---

### PQ11: Do we need terminal raw mode for password input?

**Context**: Should we switch the terminal between raw mode (for ANSI rendering) and cooked mode (for password input)?

**Answer**: **NO - getpass handles this automatically.**

**How terminal modes work**:

From Python's `termios` module and `tty` module:

```python
# Raw mode (for ANSI full-screen apps)
import tty, termios
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
tty.setraw(fd)  # Disables all processing
# ... app runs in raw mode ...
termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# Cooked mode (normal terminal)
# Default mode - line editing, echo, etc.
```

**Rich uses raw mode internally**:

Rich's Console manages terminal modes for ANSI output, but doesn't require setraw() for basic usage.

**getpass handles terminal mode switching**:

```python
# getpass.getpass() does this internally:
def unix_getpass(prompt):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = old[:]
    new[3] &= ~termios.ECHO  # Disable echo
    if echo_char:
        new[3] &= ~termios.ICANON  # Disable canonical mode
        new[3] &= ~termios.IEXTEN  # Disable extended processing
    termios.tcsetattr(fd, termios.TCSAFLUSH, new)
    
    try:
        # Read password
        passwd = _raw_input(prompt, ...)
    finally:
        # ALWAYS restore original settings
        termios.tcsetattr(fd, termios.TCSAFLUSH, old)
```

**Evidence from Python docs** ([Python Library Reference: getpass](https://docs.python.org/3/library/getpass.html)):

> "On Unix, the prompt is written to the file-like object stream using the replace error handler if needed. stream defaults to the controlling terminal (`/dev/tty`) or if that is unavailable to `sys.stderr`"

**Key insight**: When Rich's Live is running AND we're inside a pexpect PTY:

1. **Rich controls the terminal for display** (ANSI cursor positioning)
2. **pexpect controls the PTY for the subprocess** (ansbile-playbook sees PTY slave as its terminal)
3. **getpass opens /dev/tty DIRECTLY** (bypasses our PTY setup)

**So we have TWO terminal streams**:

```
Actual Terminal (/dev/tty)
    ↓
    ├─→ Python process (Rich Live running)
    │       ↓
    │   pexpect.spawn() 
    │       ↓
    │   PTY Master
    │       ↓
    │   PTY Slave (/dev/pts/X) ← ansible-playbook sees this as /dev/tty
    │
    └─→ getpass.getpass() ← opens ACTUAL /dev/tty directly
```

**The solution**:

When we call `getpass.getpass()` from our Python process:
- It opens `/dev/tty` (the ACTUAL terminal, not the PTY slave)
- It temporarily disables echo on the ACTUAL terminal
- It reads password from the ACTUAL terminal
- ansible-playbook receives the password via `child.sendline()`

**This is the "pass through" pattern**:

```python
def _handle_password_prompt(self):
    """Pass-through mode: Let terminal handle password input."""
    
    # 1. Stop our ANSI rendering
    self.live.stop()
    
    # 2. Flush any queued output
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 3. Show prompt (from pexpect buffer)
    sys.stdout.write(self.child.before.decode('utf-8'))
    sys.stdout.flush()
    
    # 4. Let getpass handle /dev/tty
    #    - getpass opens ACTUAL terminal
    #    - Disables echo temporarily
    #    - Reads from ACTUAL terminal (masked input)
    password = getpass.getpass('')
    
    # 5. Send password to ansible (via PTY master)
    self.child.sendline(password)
    
    # 6. Resume ANSI rendering
    self.live.start()
```

**Why raw mode is NOT needed**:

- Rich handles ANSI output (doesn't require raw mode for basic usage)
- getpass handles password input mode (disables echo, handles line editing)
- We just need to **stop Rich's Live display** to free terminal control

---

### PQ12: What is the simplest approach for password prompt handling?

**Context**: Maybe the simplest approach is: detect password prompt, stop ANSI status, let prompt pass through, user types, resume status. Basically "pass through" mode.

**Answer**: **YES - this IS the simplest and correct approach.**

**The "Pass Through" Pattern**:

```python
import sys
import pexpect
import getpass
from rich.live import Live
from rich.console import Console

class AnsibleRunner:
    PASSWORD_PATTERNS = [
        r'Vault password:',
        r'BECOME password:',
        r'SSH password:',
        r'\[sudo\] password for',
        r'Password:',
    ]
    
    def __init__(self):
        self.console = Console()
        self.live = None
        self.child = None
    
    def run(self, playbook: str):
        """Run ansible-playbook with compact status display."""
        
        # Compile password pattern
        patterns = self.PASSWORD_PATTERNS + [pexpect.EOF, pexpect.TIMEOUT]
        
        # Start ansible in PTY
        self.child = pexpect.spawn(
            f'ansible-playbook {playbook}',
            encoding='utf-8',
            timeout=None
        )
        
        # Start status display
        status = StatusPanel(self.child)
        self.live = Live(status, console=self.console, refresh_per_second=4)
        self.live.start()
        
        try:
            while True:
                # Read output, check for password prompts
                i = self.child.expect(patterns)
                
                if i < len(self.PASSWORD_PATTERNS):
                    # PASSWORD PROMPT DETECTED
                    self._handle_password()
                elif i == len(self.PASSWORD_PATTERNS):
                    # EOF - ansible finished
                    break
                else:
                    # TIMEOUT (shouldn't happen with timeout=None)
                    continue
        finally:
            self.live.stop()
            self.child.close()
    
    def _handle_password(self):
        """Pass through password prompt to actual terminal."""
        
        # 1. Stop status rendering (frees terminal)
        self.live.stop()
        
        # 2. Show prompt to user
        #    child.before contains text BEFORE the match
        #    The password prompt is the LAST LINE
        lines = self.child.before.strip().split('\n')
        prompt_line = lines[-1] if lines else 'Password: '
        
        # Print prompt (already shown in .before, but ensure visibility)
        # Use actual stdout (not Rich's buffer)
        sys.stdout.write(self.child.before)
        sys.stdout.flush()
        
        # 3. Get password from ACTUAL terminal
        #    getpass opens /dev/tty (the real terminal)
        #    Not the PTY that ansible sees
        #    This means the user types at ACTUAL terminal,
        #    but the password goes to ansible via sendline()
        password = getpass.getpass('')
        
        # 4. Send password to ansible (via PTY)
        self.child.sendline(password)
        
        # 5. Small delay to let ansible process password
        #    (prevent echo of password in output)
        import time
        time.sleep(0.1)
        
        # 6. Resume status rendering
        self.live.start()
```

**Why this works**:

1. **pexpect sees the prompt** in the PTY output stream
2. **We stop Rich Live** → frees actual terminal
3. **We show prompt** → user sees "Vault password:" at terminal
4. **getpass reads from /dev/tty** → actual terminal (masked input)
5. **We send password via pexpect** → ansible receives it in PTY
6. **We resume Rich Live** → status display continues

**Key insight**: We're NOT reading the password from the PTY - we're reading from the actual terminal (/dev/tty) and then forwarding it to ansible via pexpect's sendline().

**Evidence from pexpect's pxssh** (pexpect's SSH wrapper):

```python
# From pexpect/pxssh.py (pexpect's own password handling)
def login(self, server, username=None, password='', ...):
    # ...
    password = getpass.getpass('password: ')
    self.sendline(password)
```

Even pexpect's own SSH wrapper uses `getpass.getpass()` to read password, then sends it.

---

### PQ13: How to detect password prompts from ansible-playbook?

**Context**: We need to reliably detect when ansible-playbook is prompting for passwords. What patterns should we match?

**Answer**: Match specific prompts from ansible.

**Ansible password prompt patterns**:

From ansible's source code and testing:

1. **Vault password**:
   - `Vault password:`
   - `New Vault password:`
   - `Confirm New Vault password:`

2. **Become/sudo password**:
   - `BECOME password:`  (ansible default)
   - `[sudo] password for USER:`  (sudo-style)
   - `Password:` (generic fallback)

3. **SSH connection password**:
   - `SSH password:`
   - `Password:`  (SSH prompt)

4. **Remote user password**:
   - `\w+@[\w.]+\'s password:`  (SSH-style: `user@host's password:`)

**Better pattern matching**:

```python
import re

PASSWORD_PROMPTS = [
    # Vault prompts
    (r'Vault password:', 'vault'),
    (r'New Vault password:', 'new_vault'),
    (r'Confirm New Vault password:', 'confirm_vault'),
    
    # Become/sudo prompts
    (r'BECOME password:', 'become'),
    (r'\[sudo\] password for \w+:', 'sudo'),
    
    # SSH prompts
    (r'SSH password:', 'ssh'),
    (r'\w+@[\w.]+\'s password:', 'ssh_user'),
    
    # Generic password prompt (catch-all)
    (r'[Pp]assword:', 'password'),
]

def compile_patterns():
    """Compile regex patterns for pexpect."""
    patterns = [p[0] for p in PASSWORD_PROMPTS]
    patterns.extend([pexpect.EOF, pexpect.TIMEOUT])
    return patterns

def get_password_type(match_index):
    """Determine which type of password was requested."""
    if match_index < len(PASSWORD_PROMPTS):
        return PASSWORD_PROMPTS[match_index][1]
    return None
```

**Using pexpect's waitnoecho() for detection**:

```python
def detect_password_prompt(self):
    """Alternative: detect password by TTY echo disabled."""
    # pexpect's waitnoecho() blocks until subprocess disables echo
    # Most password prompts disable echo
    # Can use as NON-BLOCKING check:
    
    if self.child.waitnoecho(timeout=0.05):
        # Subprocess has disabled echo - likely password prompt
        return True
    return False

# Usage in main loop:
while True:
    # Non-blocking check: did subprocess disable echo?
    if self.detect_password_prompt():
        # Wait for actual prompt to appear in buffer
        self.child.expect('[Pp]assword:')
        self._handle_password()
        continue
    
    # Normal output processing
    i = self.child.expect(OUTPUT_PATTERNS)
    # ...
```

**Advantages of waitnoecho()**:
- Works even if prompt text varies
- Detects password prompts from any program (not just ansible)
- Based on terminal behavior (echo disabled)

**Disadvantages**:
- Requires polling (slight performance overhead)
- Some programs may disable echo for other reasons

**Hybrid approach** (best of both):

```python
def run_with_password_handling(self, playbook):
    """Run with both pattern matching AND waitnoecho detection."""
    
    patterns = compile_patterns()
    
    while True:
        # Try to read output
        try:
            # Non-blocking: check if echo disabled
            if self.child.waitnoecho(timeout=0.05):
                # Echo disabled - likely password prompt
                # Wait for the actual prompt text
                self.child.expect('[Pp]assword:', timeout=1.0)
                self._handle_password()
                continue
        except pexpect.TIMEOUT:
            pass  # No echo disable detected
        
        # Normal pattern matching
        i = self.child.expect(patterns)
        
        if i < len(PASSWORD_PROMPTS):
            # Password prompt detected
            self._handle_password()
        elif i == len(PASSWORD_PROMPTS):
            # EOF
            break
        else:
            # TIMEOUT - continue reading
            continue
```

---

### PQ14: How to handle multiple password prompts in sequence?

**Context**: User might have vault password + SSH password + become password in same run. How to handle multiple sequential prompts?

**Answer**: Handle each prompt independently, track context.

**Tracking password context**:

```python
class PasswordContext:
    """Track what passwords have been requested."""
    
    def __init__(self):
        self.vault_password = None
        self.ssh_password = None
        self.become_password = None
        self.prompts_seen = []
    
    def needs_password(self, password_type: str) -> bool:
        """Check if this password type is needed and not yet provided."""
        if password_type in self.prompts_seen:
            # Already prompted - must have been wrong password
            return True
        return True  # First time
    
    def record_prompt(self, password_type: str):
        """Record that this password was requested."""
        self.prompts_seen.append(password_type)
    
    def cache_password(self, password_type: str, password: str):
        """Cache password for reuse."""
        if password_type == 'vault':
            self.vault_password = password
        elif password_type == 'ssh':
            self.ssh_password = password
        elif password_type == 'become':
            self.become_password = password

class AnsibleRunner:
    def __init__(self):
        self.password_ctx = PasswordContext()
    
    def _handle_password(self):
        """Handle password prompt with context tracking."""
        
        # Determine password type
        password_type = self._detect_password_type()
        
        # Stop rendering
        self.live.stop()
        
        # Show prompt
        sys.stdout.write(self.child.before)
        sys.stdout.flush()
        
        # Check if we have cached password
        cached = self._get_cached_password(password_type)
        if cached and password_type not in self.password_ctx.prompts_seen:
            # Reuse cached password
            password = cached
        else:
            # Prompt user
            password = getpass.getpass('')
        
        # Record this prompt
        self.password_ctx.record_prompt(password_type)
        
        # Cache for future use
        self.password_ctx.cache_password(password_type, password)
        
        # Send to ansible
        self.child.sendline(password)
        
        # Resume rendering
        self.live.start()
    
    def _detect_password_type(self) -> str:
        """Detect which type of password is being requested."""
        last_line = self.child.before.strip().split('\n')[-1]
        
        if 'Vault' in last_line:
            return 'vault'
        elif 'BECOME' in last_line or 'sudo' in last_line:
            return 'become'
        elif 'SSH' in last_line or '@' in last_line:
            return 'ssh'
        else:
            return 'password'
    
    def _get_cached_password(self, password_type: str):
        """Get cached password if available."""
        # Could also check:
        # - Environment variables (ANSIBLE_VAULT_PASSWORD, etc.)
        # - Command-line options (--vault-password-file, etc.)
        # - ansible-vault password files
        # But for security, typically prompt user
        return None
```

**Security note**: Caching passwords in memory is convenient but has security implications. For maximum security, consider:

1. **Don't cache** - prompt for each password every time
2. **Cache only for current run** - clear after playbook finishes
3. **Use password files** - let ansible handle password files via `--vault-password-file`

**Environment variable support**:

```python
def _get_cached_password(self, password_type: str):
    """Get password from environment or cache."""
    
    env_vars = {
        'vault': 'ANSIBLE_VAULT_PASSWORD',
        'ssh': 'ANSIBLE_SSH_PASSWORD',
        'become': 'ANSIBLE_BECOME_PASSWORD',
    }
    
    # Check environment variable
    env_var = env_vars.get(password_type)
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    
    # Check cached value
    return getattr(self.password_ctx, f'{password_type}_password', None)
```

---

### PQ15: How to handle password prompts with --ask-vault-pass, --ask-become-pass flags?

**Context**: Users may pass `--ask-vault-pass` or `--ask-become-pass` to ansible-playbook, which force password prompts. How to detect these?

**Answer**: These flags cause ansible to prompt at STARTUP, before any tasks run.

**Timelines of password prompts**:

```
ansible-playbook site.yml --ask-vault-pass --ask-become-pass

Timeline:
1. ansible parses playbook
2. IF --ask-vault-pass: Prompts "Vault password:" IMMEDIATELY
3. ansible connects to hosts
4. IF --ask-become-pass: Prompts "BECOME password:" when become is needed
5. Runs tasks
```

**Detection strategy**:

```python
def run(self, playbook: str, extra_args: list = None):
    """Run with early password detection."""
    
    # Build command
    cmd = ['ansible-playbook', playbook]
    if extra_args:
        cmd.extend(extra_args)
    
    # Start ansible
    self.child = pexpect.spawn(' '.join(cmd), encoding='utf-8', timeout=None)
    
    # Start status display AFTER handling early prompts
    # (Vault password happens before any playbook output)
    
    patterns = compile_patterns()
    
    # PHASE 1: Handle early prompts (before any task output)
    # Vault password is prompted BEFORE playbook runs
    
    # Read initial output, looking for password prompts
    i = self.child.expect([r'Vault password:'] + patterns)
    
    if i == 0:
        # Vault password requested
        self._handle_password(prompt_type='vault')
        # Continue reading
        i = self.child.expect(patterns)
    
    # Start status display (after early prompts)
    self.live.start()
    
    try:
        # PHASE 2: Main loop - handle runtime prompts
        while True:
            i = self.child.expect(patterns)
            
            if i < len(PASSWORD_PROMPTS):
                password_type = get_password_type(i)
                self._handle_password(prompt_type=password_type)
            elif i == len(PASSWORD_PROMPTS):
                # EOF
                break
            else:
                # Update status display
                self._update_status(self.child.before)
    finally:
        self.live.stop()
```

**Handling password-file options**:

```python
def run(self, playbook: str, vault_password_file: str = None, 
        become_password_file: str = None):
    """Run with password file support."""
    
    cmd = ['ansible-playbook', playbook]
    
    # Use password files instead of prompting
    if vault_password_file:
        cmd.extend(['--vault-password-file', vault_password_file])
    else:
        cmd.append('--ask-vault-pass')
    
    if become_password_file:
        # ansible doesn't have --become-password-file
        # Must use --extra-vars or environment
        cmd.extend(['--extra-vars', f'ansible_become_password={read_file(become_password_file)}'])
    else:
        cmd.append('--ask-become-pass')
    
    # ... run as normal ...
```

---

### IMPLEMENTATION SUMMARY

**Best Practice Pattern for Password Handling**:

```python
import sys
import pexpect
import getpass
from rich.live import Live
from rich.console import Console
from typing import Optional

class AnsibleCompactRunner:
    """Run ansible-playbook with compact status and password handling."""
    
    PASSWORD_PATTERNS = [
        (r'Vault password:', 'vault'),
        (r'BECOME password:', 'become'),
        (r'SSH password:', 'ssh'),
        (r'\w+@[\w.]+\'s password:', 'ssh_user'),
        (r'[Pp]assword:', 'password'),
    ]
    
    def __init__(self):
        self.console = Console()
        self.live = None
        self.child = None
    
    def run(self, playbook: str, ask_vault_pass: bool = False, 
            ask_become_pass: bool = False):
        """Run ansible-playbook."""
        
        # Build command
        cmd = ['ansible-playbook', playbook]
        if ask_vault_pass:
            cmd.append('--ask-vault-pass')
        if ask_become_pass:
            cmd.append('--ask-become-pass')
        
        # Start ansible in PTY
        self.child = pexpect.spawn(
            ' '.join(cmd),
            encoding='utf-8',
            timeout=None
        )
        
        # Compile patterns
        patterns = [p[0] for p in self.PASSWORD_PATTERNS]
        patterns.extend([pexpect.EOF, pexpect.TIMEOUT])
        
        # Handle early vault password (before playbook runs)
        self._handle_early_passwords()
        
        # Start status display
        self.live = Live(self._render_status(), console=self.console, 
                         refresh_per_second=4)
        self.live.start()
        
        try:
            # Main loop
            while True:
                i = self.child.expect(patterns)
                
                if i < len(self.PASSWORD_PATTERNS):
                    # Password prompt
                    password_type = self.PASSWORD_PATTERNS[i][1]
                    self._handle_password(password_type)
                elif i == len(self.PASSWORD_PATTERNS):
                    # EOF - finished
                    break
                else:
                    # TIMEOUT - shouldn't happen
                    continue
        finally:
            self.live.stop()
            self.child.close()
    
    def _handle_early_passwords(self):
        """Handle vault/sudo passwords prompted at startup."""
        # Check for vault password (happens before playbook runs)
        try:
            i = self.child.expect([r'Vault password:', pexpect.TIMEOUT], timeout=0.5)
            if i == 0:
                self._handle_password('vault')
        except pexpect.TIMEOUT:
            pass
    
    def _handle_password(self, password_type: str):
        """Handle password prompt with pass-through to terminal."""
        
        # Stop status display (frees terminal)
        if self.live:
            self.live.stop()
        
        # Show prompt (from pexpect buffer)
        sys.stdout.write(self.child.before)
        sys.stdout.flush()
        
        # Get password from ACTUAL terminal
        password = getpass.getpass('')
        
        # Send to ansible via PTY
        self.child.sendline(password)
        
        # Small delay to prevent echo
        import time
        time.sleep(0.1)
        
        # Resume status display
        if self.live:
            self.live.start()
    
    def _render_status(self):
        """Render compact status display."""
        # ... return Rich renderable ...
        from rich.panel import Panel
        from rich.text import Text
        return Panel(Text("Running ansible-playbook..."))
```

**Key Points**:

1. **pexpect + PTY**: Runs ansible-playbook with pseudo-terminal
2. **Rich Live.stop/start**: Pauses/resumes status display
3. **getpass**: Reads from actual terminal (/dev/tty), not PTY
4. **Pattern matching**: Detects password prompts in output
5. **Pass-through pattern**: Stop rendering → prompt user → send to PTY → resume

**Alternative: pexpect's waitnoecho()**

For more robust detection (if prompts vary):

```python
def _check_password_by_echo(self) -> bool:
    """Check if subprocess disabled echo (password prompt)."""
    if self.child.waitnoecho(timeout=0.05):
        # Subprocess disabled echo - likely password
        # Read until we see the prompt
        try:
            self.child.expect('[Pp]assword:', timeout=1.0)
            return True
        except pexpect.TIMEOUT:
            pass
    return False

# In main loop:
while True:
    if self._check_password_by_echo():
        self._handle_password('unknown')
        continue
    
    i = self.child.expect(patterns)
    # ...
```

**References**:

- Python `getpass` module: https://docs.python.org/3/library/getpass.html
- Python `termios` module: https://docs.python.org/3/library/termios.html
- Python `tty` module: https://docs.python.org/3/library/tty.html
- pexpect documentation: https://pexpect.readthedocs.io/
- Rich Live documentation: https://rich.readthedocs.io/en/stable/live.html
- Stack Overflow: "How to prevent pexpect from echoing the password?"
- GitHub: pexpect/pexpect repository

---

*Password prompt research completed 2026-04-20*

---

*Password prompt handling research completed 2026-04-20*

---

## TESTING RESEARCH: Rich Live Terminal Output (2026-04-20)

### Overview

**Question**: How to write TDD tests for Python terminal applications using Rich Live for rendering (compact/default mode of AOM)?

**Context**: The compact mode uses Rich Live + ANSI cursor positioning (not Textual). We need to test:
1. Rich Live output capture
2. ANSI escape sequence verification
3. Rendering with JSONL event fixtures
4. Snapshot testing for terminal output
5. pexpect interaction testing
6. Non-TTY fallback mode
7. GitHub examples of Rich Live testing

---

### TQ1: How to capture and verify Rich Live output?

**Answer**: Use `Console.capture()` or `Console.begin_capture()` / `end_capture()`.

**Evidence from Rich Source Code** (tests/test_live.py lines 15-30):

```python
def create_capture_console(
    *, width: int = 60, height: int = 80, force_terminal: Optional[bool] = True
) -> Console:
    return Console(
        width=width,
        height=height,
        force_terminal=force_terminal,
        legacy_windows=False,
        color_system=None,  # use no color system to reduce complexity of output
        _environ={},
    )

# Example from test_growing_display():
console = create_capture_console()
console.begin_capture()
with Live(console=console, auto_refresh=False) as live:
    display = ""
    for step in range(10):
        display += f"Step {step}\n"
        live.update(display, refresh=True)
output = console.end_capture()
assert output == "\x1b[?25lStep 0\n\x1b[?25h"  # Example assertion
```

**Key Testing Patterns from Rich Test Suite**:

**Evidence**: [Rich test_live.py](https://github.com/Textualize/rich/blob/46cebbb032f920eb096efbaf23cdc6fe9dd541f7/tests/test_live.py)

1. **Create special test console**:
   ```python
   console = Console(
       width=60,
       height=80,
       force_terminal=True,  # Pretend it's a TTY
       legacy_windows=False,
       color_system=None,  # Disable colors for simpler assertions
       _environ={},  # No environment variables
   )
   ```

2. **Capture output with begin/end**:
   ```python
   console.begin_capture()
   # ... actions that write to console ...
   output = console.end_capture()
   ```

3. **Assert against exact ANSI strings**:
   ```python
   expected = "\x1b[?25lStep 0\n\r\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\n\x1b[?25h"
   assert output == expected
   ```

**Alternative: Console.capture() context manager**:

**Evidence**: [Rich test_console.py line 380](https://github.com/Textualize/rich/blob/46cebbb032f920eb096efbaf23cdc6fe9dd541f7/tests/test_console.py#L380)

```python
def test_capture() -> None:
    console = Console()
    with console.capture() as capture:
        with pytest.raises(CaptureError):
            capture.get()  # Can't call get() inside context
        console.print("Hello")
    assert capture.get() == "Hello\n"
```

**Key Differences**:

| Method | Use Case | Can call get() inside? |
|--------|----------|------------------------|
| `console.capture()` | Context manager, easy to use | No (raises CaptureError) |
| `begin_capture()` / `end_capture()` | More control, test fixtures | Yes (after end_capture()) |

---

### TQ2: How to test ANSI escape sequences in output?

**Answer**: Match ANSI codes exactly in assertions, or use `strip_ansi` helpers.

**Evidence from Rich Tests**:

From test_live.py, Rich tests match exact ANSI sequences:

```python
def test_growing_display() -> None:
    # ...
    assert (
        output
        == "\x1b[?25lStep 0\n\r\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\nStep 4\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5\nStep 6\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5\nStep 6\nStep 7\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5\nStep 6\nStep 7\nStep 8\n\r\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2K\x1b[1A\x1b[2KStep 0\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5\nStep 6\nStep 7\nStep 8\nStep 9\n\n\x1b[?25h"
    )
```

**Common ANSI Codes**:

| Code | Meaning | Usage in Tests |
|------|---------|----------------|
| `\x1b[?25l` | Hide cursor | Start of Live display |
| `\x1b[?25h` | Show cursor | End of Live display |
| `\x1b[2K` | Clear entire line | Before updating line |
| `\x1b[1A` | Move cursor up 1 line | Before clearing previous line |
| `\x1b[H` | Move cursor to home (1,1) | Start of screen update |
| `\x1b[?1049h` | Enable alternate screen buffer | Full-screen mode |
| `\x1b[?1049l` | Disable alternate screen buffer | Exit full-screen |

**Assertion Patterns**:

**Option 1: Exact match** (what Rich does):
```python
assert output == expected_with_ansi_codes
```

**Option 2: Strip ANSI, match text**:
```python
import re

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    ansi_pattern = r'\x1b\[[0-9;]*[a-zA-Z]'
    return re.sub(ansi_pattern, '', text)

def test_status_text():
    output = render_status()
    plain_text = strip_ansi(output)
    assert "Running Task 3/10" in plain_text
    assert "web1: ✔5 ⚡2" in plain_text
```

**Option 3: Check for specific ANSI codes**:
```python
def test_cursor_hidden():
    output = render_status()
    assert "\x1b[?25l" in output  # Cursor hidden
    assert "\x1b[?25h" in output  # Cursor shown (cleanup)
```

**Best Practice**: Use exact matching for integration tests, strip ANSI for unit tests focusing on content.

---

### TQ3: How to test the renderer with JSONL event fixtures?

**Answer**: Load events from JSONL files, process them, assert rendered output.

**Evidence from GitHub** (JSONL fixture patterns):

**Evidence**: [tensorzero/tensorzero tests](https://github.com/tensorzero/tensorzero/blob/main/crates/tensorzero-python/tests/conftest.py#L325)

```python
def _load_json_datapoints_from_fixture(fixture_path: Path, dataset_filter: str) -> List[CreateDatapointRequestJson]:
    """Load JSON datapoints from a JSONL fixture file."""
    datapoints = []
    with open(fixture_path) as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            # ... process datapoint ...
            datapoints.append(data)
    return datapoints
```

**Implementation for AOM**:

```python
# tests/fixtures/events.py

import json
from pathlib import Path
from aom.state import RunState
from aom.parser import parse_event

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_events_fixture(fixture_name: str) -> list[dict]:
    """Load events from a JSONL fixture file."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.jsonl"
    events = []
    
    with open(fixture_path) as f:
        for line in f:
            if not line.strip():
                continue
            events.append(json.loads(line))
    
    return events

def apply_events_to_state(events: list[dict]) -> RunState:
    """Apply fixture events to a fresh RunState."""
    state = RunState()
    for event_data in events:
        event = parse_event(event_data)
        state.handle_event(event)
    return state

# tests/fixtures/simple_playbook.jsonl
"""
{"event_type": "playbook_start", "playbook": "site.yml", "timestamp": "2026-04-20T10:00:00Z"}
{"event_type": "play_start", "play": "Configure Webservers", "hosts": ["web1", "web2"]}
{"event_type": "task_start", "task": "Install nginx", "host": "web1"}
{"event_type": "task_completed", "task": "Install nginx", "host": "web1", "status": "changed"}
{"event_type": "task_start", "task": "Install nginx", "host": "web2"}
{"event_type": "task_completed", "task": "Install nginx", "host": "web2", "status": "ok"}
{"event_type": "play_completed", "play": "Configure Webservers"}
{"event_type": "playbook_completed", "playbook": "site.yml"}
"""
```

**Testing Pattern**:

```python
# tests/test_renderer_unit.py

import pytest
from aom.renderer import CompactRenderer
from tests.fixtures.events import load_events_fixture, apply_events_to_state

def test_renderer_shows_running_tasks():
    """Test that renderer shows currently running tasks."""
    # Load fixture with running tasks
    events = load_events_fixture("single_running_task")
    state = apply_events_to_state(events)
    
    # Render status
    renderer = CompactRenderer(state)
    output = renderer.render()
    
    # Assertions (strip ANSI for readability)
    plain = strip_ansi(output)
    assert "⏵ web1: Install nginx" in plain
    assert "Task 3/10" in plain

def test_renderer_shows_host_summary():
    """Test that renderer shows per-host stats."""
    events = load_events_fixture("multi_host_completed")
    state = apply_events_to_state(events)
    
    renderer = CompactRenderer(state)
    output = renderer.render()
    
    plain = strip_ansi(output)
    assert "web1: ✔5 ⚡2 ❌0" in plain
    assert "web2: ✔3 ⚡0 ❌1" in plain

def test_renderer_handles_no_running_tasks():
    """Test renderer when no tasks are running."""
    events = load_events_fixture("all_tasks_completed")
    state = apply_events_to_state(events)
    
    renderer = CompactRenderer(state)
    output = renderer.render()
    
    # Should show summary, not "no running tasks" message
    plain = strip_ansi(output)
    assert "✔ Completed" in plain or "Task 10/10" in plain
```

**Pytest Fixture Approach**:

```python
# tests/conftest.py

import pytest
from pathlib import Path
from aom.state import RunState
from aom.parser import parse_event
import json

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def load_events(fixtures_dir):
    def _load(fixture_name: str) -> RunState:
        """Load events from fixture and return populated RunState."""
        fixture_path = fixtures_dir / f"{fixture_name}.jsonl"
        state = RunState()
        
        with open(fixture_path) as f:
            for line in f:
                if not line.strip():
                    continue
                event_data = json.loads(line)
                event = parse_event(event_data)
                state.handle_event(event)
        
        return state
    
    return _load

# Usage in tests:
def test_with_fixture(load_events):
    state = load_events("simple_playbook")
    # ... test state ...
```

---

### TQ4: Is there a pytest plugin for snapshot testing terminal output?

**Answer**: YES - use **inline-snapshot** or **syrupy**.

**Evidence from Pydantic Blog** ([Better Python tests with inline-snapshot](https://pydantic.dev/articles/inline-snapshot)):

**What is Snapshot Testing?**

Snapshot testing captures the expected output once, saves it, and compares future runs against it. Perfect for:
- Complex rendered output
- Large data structures
- Terminal ANSI output

**Option 1: inline-snapshot** (Recommended for terminal output):

**Evidence**: [15r10nk/inline-snapshot GitHub](https://github.com/15r10nk/inline-snapshot)

```python
from inline_snapshot import snapshot

def test_rendered_output():
    output = render_status(state)
    assert output == snapshot()
```

Run with `pytest --inline-snapshot=fix` to auto-generate snapshots:

```python
def test_rendered_output():
    output = render_status(state)
    assert output == snapshot("""\
\x1b[?25l
⏱ 2m34s
Task 8/10: Install nginx
web1: ✔5 ⚡2 ❌0 | db1: ✔3 ❌1
\x1b[?25h
""")
```

**Key Features**:
- Snapshots stored INLINE in source code
- Auto-update with `--inline-snapshot=fix`
- Supports external files with `outsource()`
- Works with any string (including ANSI)

**Installation**:
```bash
pip install inline-snapshot
```

**Option 2: syrupy** (External snapshot files):

**Evidence**: [tophat/syrupy GitHub](https://github.com/tophat/syrupy)

```python
def test_rendered_output(snapshot):
    output = render_status(state)
    assert output == snapshot
```

Snapshots stored in `tests/__snapshots__/test_renderer.ambr`:

```ambr
# serializer version: 1
# name: test_rendered_output
  \x1b[?25l
  ⏱ 2m34s
  Task 8/10: Install nginx
  web1: ✔5 ⚡2 ❌0 | db1: ✔3 ❌1
  \x1b[?25h
# ---
```

**Comparison**:

| Feature | inline-snapshot | syrupy |
|---------|------------------|--------|
| Snapshot location | Inline in source | Separate files |
| Update command | `--inline-snapshot=fix` | `--snapshot-update` |
| Setup | No fixture needed | `snapshot` fixture |
| Best for | Small/medium output | Large output |
| CI-friendly | Yes (in source) | Yes (committed files) |

**Recommendation for AOM**:

**Use inline-snapshot** because:
1. Terminal output is small to medium size (~10-50 lines)
2. Snapshot visible in test source (better documentation)
3. Easy to update when renderer changes
4. Works seamlessly with ANSI codes

**Example Test File**:

```python
# tests/test_renderer_snapshots.py

from inline_snapshot import snapshot
from aom.renderer import CompactRenderer
from tests.fixtures.events import load_events_fixture, apply_events_to_state

def test_renderer_no_tasks(snapshot):
    """Snapshot: renderer with no running tasks."""
    events = load_events_fixture("no_running_tasks")
    state = apply_events_to_state(events)
    output = CompactRenderer(state).render()
    
    assert output == snapshot()

def test_renderer_single_running_task(snapshot):
    """Snapshot: renderer with one running task."""
    events = load_events_fixture("single_running_task")
    state = apply_events_to_state(events)
    output = CompactRenderer(state).render()
    
    assert output == snapshot()

def test_renderer_multi_host(snapshot):
    """Snapshot: renderer with multiple hosts."""
    events = load_events_fixture("multi_host_mixed")
    state = apply_events_to_state(events)
    output = CompactRenderer(state).render()
    
    assert output == snapshot()

# After running pytest --inline-snapshot=fix:
# The snapshots are auto-generated in the test file!
```

---

### TQ5: How to unit-test the pexpect + Rich Live interaction?

**Answer**: Mock pexpect, test the rendering logic separately from PTY interaction.

**Testing Strategy**:

1. **Unit test rendering logic** (no pexpect, just state → output)
2. **Integration test with pexpect** (real or mock subprocess)
3. **System test** (actual ansible-playbook)

**Evidence from pytest-subprocess**:

**Evidence**: [pytest-subprocess documentation](https://pytest-subprocess.readthedocs.io/)

```python
def test_process(fp):
    fp.register(["ansible-playbook", "site.yml"])
    process = subprocess.run(["ansible-playbook", "site.yml"])
    assert process.returncode == 0
```

**Unit Test (State → Rendering)**:

```python
# tests/test_renderer_unit.py

from aom.state import RunState, TaskState, Status
from aom.renderer import CompactRenderer

def test_renderer_single_running_task():
    """Unit test: render state with one running task."""
    # Create state manually
    state = RunState()
    state.elapsed_time = 125.0  # 2m5s
    state.current_play = "Configure Webservers"
    state.current_task = TaskState(
        name="Install nginx",
        host="web1",
        status=Status.RUNNING,
        duration=15.0
    )
    state.host_stats = {
        "web1": {"ok": 5, "changed": 2, "failed": 0},
        "web2": {"ok": 3, "changed": 0, "failed": 1}
    }
    
    # Render
    renderer = CompactRenderer(state)
    output = renderer.render()
    
    # Assertions
    plain = strip_ansi(output)
    assert "⏱ 2m5s" in plain
    assert "⏵ web1: Install nginx" in plain
    assert "web1: ✔5 ⚡2 ❌0" in plain
```

**Integration Test (Mock pexpect)**:

```python
# tests/test_runner_integration.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from aom.runner import AnsibleRunner

def test_runner_handles_password_prompt():
    """Integration test: password prompt detection and handling."""
    runner = AnsibleRunner()
    
    # Mock pexpect.spawn
    mock_child = Mock()
    mock_child.expect = Mock(side_effect=[
        0,  # First call: password prompt detected (index 0)
        3   # Second call: EOF (index 3)
    ])
    mock_child.before = "Vault password:"
    mock_child.sendline = Mock()
    
    with patch('pexpect.spawn', return_value=mock_child):
        with patch('getpass.getpass', return_value='secret123'):
            runner.run('site.yml')
    
    # Assertions
    assert mock_child.sendline.called
    assert mock_child.sendline.call_args[0][0] == 'secret123'

def test_runner_updates_state_from_output():
    """Integration test: state updated from parsed output."""
    runner = AnsibleRunner()
    
    # Mock pexpect with pre-recorded output
    mock_child = Mock()
    mock_child.expect = Mock(side_effect=[
        3,  # EOF after processing
    ])
    mock_child.before = '{"event_type": "task_start", "task": "Install nginx", "host": "web1"}'
    
    with patch('pexpect.spawn', return_value=mock_child):
        runner.run('site.yml')
    
    # State should be updated
    assert runner.state.current_task.name == "Install nginx"
    assert runner.state.current_task.host == "web1"
```

**Testing Rich Live.stop() / Live.start()**:

```python
# tests/test_live_control.py

from rich.live import Live
from rich.console import Console
from io import StringIO
import time

def test_live_stop_frees_terminal():
    """Test that Live.stop() frees the terminal for user input."""
    console = Console(file=StringIO(), force_terminal=True)
    
    live = Live("Status", console=console)
    live.start()
    
    # Live is running
    assert live._started
    
    # Stop it
    live.stop()
    
    # Live is stopped
    assert not live._started
    
    # Console should be usable again
    console.print("User input")
    assert "User input" in console.file.getvalue()

def test_live_restart_after_stop():
    """Test that Live can be restarted after stopping."""
    console = Console(file=StringIO(), force_terminal=True)
    
    live = Live("Status", console=console)
    live.start()
    assert live._started
    
    live.stop()
    assert not live._started
    
    # Restart
    live.start()
    assert live._started
```

---

### TQ6: How to test non-TTY (piped) fallback mode?

**Answer**: Create Console with `force_terminal=False` or test `sys.stdout.isatty() == False`.

**Evidence from Rich Tests**:

**Evidence**: [test_live.py line 173](https://github.com/Textualize/rich/blob/46cebbb032f920eb096efbaf23cdc6fe9dd541f7/tests/test_live.py#L173)

```python
def test_growing_display_file_console() -> None:
    """Test Live when console is not a terminal (file output)."""
    console = create_capture_console(force_terminal=False)
    console.begin_capture()
    with Live(console=console, auto_refresh=False) as live:
        display = ""
        for step in range(10):
            display += f"Step {step}\n"
            live.update(display, refresh=True)
    output = console.end_capture()
    # No ANSI codes when not a terminal
    assert (
        output
        == "Step 0\nStep 1\nStep 2\nStep 3\nStep 4\nStep 5\nStep 6\nStep 7\nStep 8\nStep 9\n"
    )
```

**Key Insight**:

When `Console(force_terminal=False)`:
- Rich **does NOT emit ANSI escape codes**
- Output is plain text
- Live display works but without cursor positioning

**For AOM Testing**:

```python
# tests/test_renderer_nontty.py

from rich.console import Console
from io import StringIO
from aom.renderer import CompactRenderer
from aom.state import RunState

def test_renderer_non_tty_mode():
    """Test renderer when stdout is not a TTY (e.g., piped)."""
    # Simulate non-TTY
    console = Console(file=StringIO(), force_terminal=False)
    
    # Create state
    state = RunState()
    state.elapsed_time = 120.0
    state.host_stats = {"web1": {"ok": 5, "changed": 2}}
    
    # Render to non-TTY console
    renderer = CompactRenderer(state, console=console)
    renderer.render()
    
    # Output should have NO ANSI codes
    output = console.file.getvalue()
    assert "\x1b[" not in output  # No ANSI escape codes
    assert "⏱" not in output  # No Unicode that requires terminal
    assert "web1: 5 tasks, 2 changed" in output

def test_renderer_respects_no_color_env():
    """Test that renderer respects NO_COLOR environment variable."""
    import os
    os.environ['NO_COLOR'] = '1'
    
    try:
        console = Console()
        assert not console._color_system  # Should be None or False
    finally:
        del os.environ['NO_COLOR']

def test_renderer_final_summary_non_tty():
    """Test final summary output for non-TTY (piped to file/grep)."""
    console = Console(file=StringIO(), force_terminal=False)
    
    state = RunState()
    state.host_stats = {
        "web1": {"ok": 5, "changed": 2, "failed": 0},
        "web2": {"ok": 3, "changed": 0, "failed": 1}
    }
    
    renderer = CompactRenderer(state, console=console)
    renderer.print_final_summary()
    
    output = console.file.getvalue()
    
    # Should look like ansible-playbook's PLAY RECAP
    assert "PLAY RECAP" in output
    assert "web1 : ok=5 changed=2 failed=0" in output
    assert "web2 : ok=3 changed=0 failed=1" in output
```

---

### TQ7: GitHub examples of testing Rich Live rendering?

**Answer**: The Rich project itself has excellent test examples.

**Evidence from Rich Test Suite**:

**File**: [tests/test_live.py](https://github.com/Textualize/rich/blob/46cebbb032f920eb096efbaf23cdc6fe9dd541f7/tests/test_live.py) (Commit: 46cebbb)

**Key Test Cases**:

1. **test_live_state** - Tests start/stop lifecycle
2. **test_growing_display** - Tests incremental output with ANSI codes
3. **test_growing_display_transient** - Tests transient mode (output disappears after)
4. **test_growing_display_overflow_ellipsis** - Tests vertical overflow handling
5. **test_growing_display_file_console** - Tests non-TTY mode
6. **test_live_screen** - Tests alternate screen buffer
7. **test_growing_display_console_redirect** - Tests console.print() above Live

**Example from test_live_screen**:

```python
def test_live_screen() -> None:
    """Test Live with alternate screen buffer."""
    console = create_capture_console(width=20, height=5)
    console.begin_capture()
    with Live(Text("foo"), screen=True, console=console, auto_refresh=False) as live:
        live.refresh()
    result = console.end_capture()
    
    expected = "\x1b[?1049h\x1b[H\x1b[?25l\x1b[Hfoo                 \n                    \n                    \n                    \n                    \x1b[Hfoo                 \n                    \n                    \n                    \n                    \x1b[?25h\x1b[?1049l"
    assert result == expected
```

**Other Projects Using Rich Live Testing**:

**Evidence**: [PyTorch/XLA tests](https://github.com/pytorch/xla/blob/master/test/spmd/test_spmd_debugging.py#L34)

```python
def test_debugging_spmd_single_host_tiled_tpu(self):
    from torch_xla.distributed.spmd.debugging import visualize_sharding
    sharding = '{devices=[2,4]0,1,2,3,4,5,6,7}'
    generated_table = visualize_sharding(sharding)
    console = rich.console.Console()
    with console.capture() as capture:
        console.print(generated_table)
    output = capture.get()
    
    # Compare with expected output
    assert output == fake_output
```

**Evidence**: [microsoft/apm tests](https://github.com/microsoft/apm/blob/main/src/apm_cli/output/formatters.py#L302)

```python
# Render table to lines
if self.console:
    with self.console.capture() as capture:
        self.console.print(table)
    table_output = capture.get()
    if table_output.strip():
        lines.extend(table_output.split('\n'))
```

**Best Practices from These Examples**:

1. **Always use `console.capture()`** for testing
2. **Use `force_terminal=True`** to force ANSI codes in tests
3. **Use `color_system=None`** to simplify assertions
4. **Match exact ANSI strings** for integration tests
5. **Strip ANSI** for content-focused unit tests
6. **Test both TTY and non-TTY modes**

---

### Recommended Test Structure for AOM

Based on the research, here's the recommended test structure:

```
tests/
├── conftest.py                      # Pytest fixtures
│   ├── fixtures_dir
│   ├── load_events
│   └── capture_console
│
├── fixtures/                        # JSONL event fixtures
│   ├── minimal_playbook.jsonl
│   ├── single_running_task.jsonl
│   ├── multi_host_mixed.jsonl
│   ├── password_prompt.jsonl
│   └── non_tty_output.jsonl
│
├── test_renderer_unit.py            # Unit tests (state → output)
│   ├── test_renderer_shows_running_tasks
│   ├── test_renderer_shows_host_summary
│   ├── test_renderer_handles_empty_state
│   └── test_renderer_formatting
│
├── test_renderer_snapshots.py       # Snapshot tests (inline-snapshot)
│   ├── test_renderer_no_tasks
│   ├── test_renderer_single_running_task
│   ├── test_renderer_multi_host
│   └── test_renderer_completed_playbook
│
├── test_renderer_ansi.py            # ANSI code tests
│   ├── test_ansi_cursor_hide_show
│   ├── test_ansi_sequence_correctness
│   └── test_ansi_clearing
│
├── test_runner_integration.py       # Integration tests (pexpect)
│   ├── test_runner_handles_password_prompt
│   ├── test_runner_updates_state_from_output
│   ├── test_runner_live_stop_start
│   └── test_runner_signal_handling
│
├── test_renderer_nontty.py           # Non-TTY mode tests
│   ├── test_renderer_non_tty_mode
│   ├── test_renderer_no_color_env
│   ├── test_renderer_final_summary
│   └── test_renderer_piped_output
│
└── test_live_control.py             # Rich Live control tests
    ├── test_live_start_stop
    ├── test_live_console_print
    └── test_live_error_recovery
```

---

### Implementation Checklist

**Phase 1: Unit Testing Setup**

- [ ] Install test dependencies: `pytest`, `inline-snapshot`, `pytest-mock`
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Create example JSONL fixtures in `tests/fixtures/`
- [ ] Implement `load_events_fixture()` helper
- [ ] Write first unit test for renderer

**Phase 2: Snapshot Testing**

- [ ] Install `inline-snapshot`: `pip install inline-snapshot`
- [ ] Create `test_renderer_snapshots.py`
- [ ] Run `pytest --inline-snapshot=fix` to generate initial snapshots
- [ ] Commit snapshot files

**Phase 3: Integration Testing**

- [ ] Mock pexpect.spawn for integration tests
- [ ] Test password prompt handling
- [ ] Test state updates from parsed output
- [ ] Test Rich Live stop/start cycle

**Phase 4: Non-TTY Testing**

- [ ] Test with `force_terminal=False`
- [ ] Test with `NO_COLOR` environment variable
- [ ] Test final summary output for piped mode

**Phase 5: CI/CD Integration**

- [ ] Add test run to CI pipeline
- [ ] Add coverage reporting
- [ ] Add snapshot update command for PRs

---

### References

**Official Documentation**:
- Rich Console API: https://rich.readthedocs.io/en/stable/console.html
- Rich Live API: https://rich.readthedocs.io/en/stable/live.html
- inline-snapshot: https://15r10nk.github.io/inline-snapshot/
- syrupy: https://tophat.github.io/syrupy/

**Rich Test Suite** (Excellent examples):
- test_live.py: https://github.com/Textualize/rich/blob/master/tests/test_live.py
- test_console.py: https://github.com/Textualize/rich/blob/master/tests/test_console.py
- test_progress.py: https://github.com/Textualize/rich/blob/master/tests/test_progress.py

**GitHub Examples**:
- PyTorch/XLA Rich Console testing: https://github.com/pytorch/xla/blob/master/test/spmd/test_spmd_debugging.py
- Microsoft APM formatter tests: https://github.com/microsoft/apm/blob/main/src/apm_cli/output/formatters.py

**Related Testing Tools**:
- pytest-subprocess: https://pytest-subprocess.readthedocs.io/
- pytest-mock: https://pytest-mock.readthedocs.io/

---

*Testing research completed 2026-04-20*

## NEW QUESTIONS - TUI Features Research (2026-04-20)

### GQ1: Inspect TUI - How to create a readonly Textual TUI that reuses main TUI components?

- **Context**: `aom inspect --tui <session>` should open a readonly Textual TUI for browsing a saved session. Should reuse Tree, Log, Summary widgets but without action buttons (no run/re-run controls).

- **Evidence from Textual Documentation and Code Examples**:

#### **Textual ModalScreen for Readonly Views**

**Evidence**: [Textual screen.py](https://github.com/Textualize/textual/blob/main/src/textual/screen.py) line 2205:

```python
class ModalScreen(Screen[ScreenResultType]):
    """A screen with bindings that take precedence over the App's key bindings.
    The default styling of a modal screen will dim the screen underneath.
    """
```

**Pattern**: Use `Screen` or `ModalScreen` subclass with readonly widgets.

#### **Disabling Interactive Widgets**

**Evidence**: Textual widgets support `disabled` property and `can_focus`:

From grep search results:
```python
# Widget can be made non-interactive
disabled=True  # Disables all interaction
can_focus=False  # Prevents keyboard focus
```

**Example Pattern**:
```python
from textual.widgets import Tree, Button

class ReadonlyTree(Tree):
    """Tree widget without action buttons."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disabled = False  # Allow navigation
        self.can_focus = True
    
    def compose(self):
        # Don't include action buttons
        yield from super().compose()
        # NO: yield Button("Run", id="run-btn")
```

#### **Component Reuse Strategy**

**Evidence**: From [Textual screens guide](https://textual.textualize.io/guide/screens/):

**Pattern**: Create a base screen class with shared components:

```python
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Tree, RichLog, Static

# Shared widgets (used by both main TUI and inspect TUI)
class TaskTree(Tree):
    """Tree widget for plays/tasks/hosts."""
    
    def __init__(self, state: RunState, readonly: bool = False):
        self.state = state
        self.readonly = readonly
        super().__init__()
    
    def compose(self) -> ComposeResult:
        yield from self._render_tree()
        
        # Only show action buttons if NOT readonly
        if not self.readonly:
            yield Button("Re-run", id="rerun-btn")
            yield Button("Filter", id="filter-btn")


class LogPanel(RichLog):
    """Log panel - same for both modes."""
    # RichLog is inherently readonly for past events
    pass


class SummaryPanel(Static):
    """Summary panel - readonly by default."""
    pass


# Main TUI screen (interactive)
class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield TaskTree(self.app.state, readonly=False)
        yield LogPanel()
        yield SummaryPanel()


# Inspect TUI screen (readonly)
class InspectScreen(Screen):
    """Readonly screen for browsing saved sessions."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Exit", priority=True),
        Binding("q", "app.quit", "Quit", priority=True),
        # Navigation works, but no run/rerun bindings
    ]
    
    def __init__(self, session_id: str, artifact_path: Path):
        self.session_id = session_id
        self.artifact_path = artifact_path
        self.state = self._load_session()
        super().__init__()
    
    def compose(self) -> ComposeResult:
        # Reuse same widgets with readonly=True
        yield TaskTree(self.state, readonly=True)
        yield LogPanel()
        yield SummaryPanel()
    
    def _load_session(self) -> RunState:
        """Load session from .aom artifact file."""
        # Read artifact (JSONL format)
        events = []
        with open(self.artifact_path) as f:
            for line in f:
                event = json.loads(line)
                if event.get("type") == "event":
                    events.append(event)
        
        # Replay events into state machine
        state = RunState()
        for event in events:
            state.handle_event(event)
        
        return state
```

#### **Navigation in Readonly Mode**

**Evidence**: Tree navigation works the same in readonly mode:

```python
BINDINGS = [
    Binding("up", "cursor_up", "Up", show=False),
    Binding("down", "cursor_down", "Down", show=False),
    Binding("right", "select_cursor", "Expand", show=False),
    Binding("left", "select_cursor", "Collapse", show=False),
    Binding("enter", "toggle_node", "Toggle"),
    # Search/filter also work
    Binding("slash", "focus_search", "Search"),
]
```

Navigation and search/filter work fine in readonly mode - just no "execute" actions.

#### **Hiding Action Buttons in Readonly Mode**

**CSS approach** (recommended):

```css
/* In inspect mode, hide action buttons */
InspectScreen Button {
    display: none;
}

/* Or use conditional class */
.readonly Button {
    display: none;
}
```

**Python approach**:

```python
def compose(self) -> ComposeResult:
    yield TaskTree(self.state)
    yield LogPanel()
    yield SummaryPanel()
    
    # Conditionally add action buttons
    if not self.readonly:
        yield ActionBar()  # Container with Run/Filter buttons
```

- **Implementation Recommendation**:

**Architecture**:

```python
# widgets/task_tree.py
class TaskTree(Tree):
    """Shared tree widget for both main TUI and inspect TUI."""
    
    def __init__(self, state: RunState, readonly: bool = False):
        self.state = state
        self.readonly = readonly
        super().__init__()
    
    def render_node(self, node: TreeNode) -> RenderableType:
        """Render tree node (same for both modes)."""
        return self._format_node(node)
    
    def on_mount(self):
        """Populate tree with state data."""
        self._build_tree_from_state()


# screens/inspect.py
class InspectScreen(Screen):
    """Readonly TUI for browsing saved sessions."""
    
    CSS_PATH = "inspect.tcss"  # Specific CSS for inspect mode
    
    BINDINGS = [
        Binding("escape,q", "app.pop_screen", "Close", priority=True),
        Binding("ctrl+f", "app.push_screen('search')", "Search"),
        Binding("up,down", "cursor_up|cursor_down", "Navigate"),
        # NO: Binding("shift+r", "rerun", "Re-run")
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield TaskTree(self.state, readonly=True)
            yield LogPanel()
            yield SummaryPanel()
        yield Footer()
```

**Loading Session Data**:

```python
def load_session_from_artifact(artifact_path: Path) -> RunState:
    """Load RunState from .aom artifact file."""
    
    state = RunState()
    
    with open(artifact_path) as f:
        for line in f:
            entry = json.loads(line)
            
            if entry.get("type") == "metadata":
                state.playbook = entry.get("playbook")
                state.version = entry.get("version")
            
            elif entry.get("type") == "event":
                # Replay event through state machine
                state.handle_event(entry)
            
            elif entry.get("type") == "stats":
                state.stats = entry
    
    return state
```

### GQ2: Re-run Dialog - How to create Shift+R dialog for modifying ansible-playbook arguments?

- **Context**: `Shift+R` opens a dialog to modify ansible-playbook arguments before re-running. What should this look like? Single editable command line string or structured fields?

- **Evidence from Textual Documentation and Real-World Examples**:

#### **ModalScreen for Complex Forms**

**Evidence**: Multiple examples of ModalScreen with Input widgets:

From [mathspp blog](https://mathspp.com/blog/how-to-use-modal-screens-in-textual):

```python
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label

class InputModalScreen(ModalScreen[str]):
    """A modal screen that returns a string result."""
    
    def __init__(self, title: str, label: str, placeholder: str = ""):
        self.title = title
        self.label = label
        self.placeholder = placeholder
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Label(self.label)
            yield Input(placeholder=self.placeholder, id="input")
            yield Button("OK", variant="success", id="ok")
            yield Button("Cancel", variant="error", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            input_widget = self.query_one(Input)
            self.dismiss(input_widget.value)  # Pass result back
        else:
            self.dismiss(None)  # Cancel
```

#### **Command Line String vs Structured Fields**

**Two approaches**:

**A) Single Command Line String** (simpler):

```python
class RerunDialog(ModalScreen[str]):
    """Dialog with editable command line."""
    
    CSS = """
    RerunDialog {
        align: center middle;
    }
    #dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
    }
    Input {
        width: 100%;
    }
    """
    
    def __init__(self, current_args: list[str]):
        self.current_args = current_args
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("ansible-playbook command:")
            yield Input(
                value=" ".join(self.current_args),
                id="cmd-input"
            )
            with Horizontal():
                yield Button("Run", variant="success", id="run")
                yield Button("Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            cmd = self.query_one(Input).value
            # Parse into list: ["ansible-playbook", "playbook.yml", ...]
            args = shlex.split(cmd)
            self.dismiss(args)
        else:
            self.dismiss(None)
```

**Pros**: Simple, familiar to users, full control
**Cons**: No validation, no help text, syntax errors possible

**B) Structured Fields** (more guided):

```python
from textual.widgets import Input, Select, Checkbox

class RerunDialogStructured(ModalScreen[dict]):
    """Dialog with structured fields."""
    
    CSS = """
    RerunDialogStructured {
        align: center middle;
    }
    #dialog {
        width: 80;
        border: thick $primary;
        padding: 1;
    }
    """
    
    def __init__(self, current_config: dict):
        self.current_config = current_config
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Playbook:")
            yield Input(value=self.current_config.get("playbook", ""), id="playbook")
            
            yield Label("Inventory:")
            yield Input(value=self.current_config.get("inventory", ""), id="inventory")
            
            yield Label("Limit to hosts:")
            yield Input(value=self.current_config.get("limit", ""), id="limit", placeholder="host1,host2")
            
            yield Label("Tags:")
            yield Input(value=self.current_config.get("tags", ""), id="tags", placeholder="tag1,tag2")
            
            yield Label("Extra vars:")
            yield Input(value=self.current_config.get("extra_vars", ""), id="extra_vars", placeholder="key=value")
            
            with Horizontal():
                yield Checkbox(self.current_config.get("verbose", False), label="Verbose (-v)", id="verbose")
                yield Checkbox(self.current_config.get("check", False), label="Check mode (--check)", id="check")
                yield Checkbox(self.current_config.get("diff", False), label="Diff (--diff)", id="diff")
            
            with Horizontal():
                yield Button("Run", variant="success", id="run")
                yield Button("Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            config = self._collect_config()
            self.dismiss(config)
        else:
            self.dismiss(None)
    
    def _collect_config(self) -> dict:
        """Collect values from all input widgets."""
        return {
            "playbook": self.query_one("#playbook", Input).value,
            "inventory": self.query_one("#inventory", Input).value,
            "limit": self.query_one("#limit", Input).value,
            "tags": self.query_one("#tags", Input).value,
            "extra_vars": self.query_one("#extra_vars", Input).value,
            "verbose": self.query_one("#verbose", Checkbox).value,
            "check": self.query_one("#check", Checkbox).value,
            "diff": self.query_one("#diff", Checkbox).value,
        }
```

**Pros**: Validation possible, help text, structured
**Cons**: Limited flexibility, more code

#### **Validation**

**Evidence**: From Textual Input validation docs:

```python
from textual.validation import Number, Function, ValidationResult

# Built-in validators
Input(validators=[Number(minimum=1, maximum=100)])

# Custom validator
class PlaybookPath(Validator):
    def validate(self, value: str) -> ValidationResult:
        path = Path(value)
        if not path.exists():
            return self.failure(f"Playbook not found: {value}")
        if not value.endswith(('.yml', '.yaml')):
            return self.failure("Must be a YAML file")
        return self.success()

# Use in dialog
yield Input(validators=[PlaybookPath()], id="playbook")
```

Validation runs on:
- `changed`: Every keystroke (real-time)
- `submitted`: When Enter pressed
- `blur`: When focus leaves input

**Recommendation**: Use `"submitted"` validation only (don't nag during typing):
```python
Input(validators=[...], validate_on=["submitted"])
```

#### **Preserving Session State**

**Pattern**: Don't clear current state, start new run:

```python
class MainScreen(Screen):
    def action_rerun(self) -> None:
        """Re-run playbook (Shift+R)."""
        def handle_rerun(new_args: list[str] | None) -> None:
            if new_args:
                # Start new run WITHOUT clearing state
                # Previous session saved in artifacts already
                asyncio.create_task(self.app.start_playbook(new_args))
        
        # Show dialog
        self.app.push_screen(RerunDialog(self.current_args), handle_rerun)
    
    def action_rerun_modified(self) -> None:
        """Re-run with modified args (Shift+R)."""
        def handle_modified(config: dict | None) -> None:
            if config:
                args = self._build_args_from_config(config)
                asyncio.create_task(self.app.start_playbook(args))
        
        self.app.push_screen(RerunDialogStructured(self.current_config), handle_modified)
```

#### **Rolling History Pattern**

**Pattern**: Keep track of previous arg modifications:

```python
class AppConfig(BaseSettings):
    rerun_history: list[dict] = Field(default_factory=list, max_length=20)
    
    def add_to_history(self, config: dict):
        """Add config to history (max 20 entries)."""
        self.rerun_history.append(config)
        if len(self.rerun_history) > 20:
            self.rerun_history.pop(0)
    
    def get_last_config(self) -> dict | None:
        """Get most recent config."""
        return self.rerun_history[-1] if self.rerun_history else None
```

**UI Pattern**: Show history in dialog:

```python
class RerunDialogWithHistory(ModalScreen[dict]):
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Recent runs:")
            yield ListView(
                [ListItem(Label(self._format_config(c))) for c in self.app.config.rerun_history[-5:]],
                id="history"
            )
            yield Label("Modify args:")
            yield Input(value=self._current_args_str(), id="cmd-input")
            # ...
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """User selected from history - populate input."""
        selected_config = self.app.config.rerun_history[event.item_index]
        self.query_one(Input).value = self._format_config(selected_config)
```

- **Implementation Recommendation**:

**Recommendation**: Use **hybrid approach**:

1. **Default (Shift+R)**: Show structured form with common fields
2. **Advanced (Ctrl+Shift+R or button)**: Full command line editor

**Implementation**:

```python
# screens/rerun_dialog.py
class RerunDialog(ModalScreen[list[str]]):
    """Dialog for re-running playbook with modified args."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel", priority=True),
        Binding("enter", "submit", "Run", show=False),
        Binding("tab", "focus_next", show=False),
    ]
    
    def __init__(self, current_args: list[str], history: list[dict]):
        self.current_args = current_args
        self.history = history
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            # Show last 3 runs for quick selection
            if self.history:
                yield Label("Recent:")
                for hist in self.history[-3:]:
                    yield Button(
                        self._format_config_short(hist),
                        id=f"hist-{len(self.history) - 3 + i}"
                    )
            
            # Main input
            yield Label("Command:")
            yield Input(
                value="ansible-playbook " + " ".join(self.current_args),
                id="cmd-input",
                suggester=CommandSuggester()
            )
            
            # Buttons
            with Horizontal():
                yield Button("Run", variant="success", id="run")
                yield Button("Edit Fields", id="edit-fields")
                yield Button("Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            self._submit()
        elif event.button.id == "edit-fields":
            # Switch to structured view
            self.app.push_screen(RerunFormDialog(self.current_args, self.history))
        elif event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id.startswith("hist-"):
            # Use historical config
            idx = int(event.button.id.split("-")[1])
            config = self.history[idx]
            self.query_one(Input).value = self._format_config(config)
    
    def _submit(self):
        """Parse and return command."""
        cmd = self.query_one(Input).value
        try:
            args = shlex.split(cmd)
            # Remove "ansible-playbook" if present
            if args[0] == "ansible-playbook":
                args = args[1:]
            self.dismiss(args)
        except ValueError as e:
            self.notify(f"Invalid command: {e}", severity="error")


class RerunFormDialog(ModalScreen[dict]):
    """Structured form for advanced re-run options."""
    
    # Similar structure but with individual fields...
    # (see structured example above)
```

**Key Features**:
1. Quick selection from history
2. Command line editing with validation
3. Structured fields for common options
4. Validation on submit
5. Save to history on successful run

### GQ3: How to load session data from .aom artifact files into the state machine?

- **Context**: Inspect TUI needs to load saved session data (JSONL format) into RunState for display.

- **Evidence from Specification**:

**Artifact Format** (from SPECIFICATION.md lines 839-853):

```jsonl
{"type": "metadata", "playbook": "site.yml", "version": "1.0", "created": "2026-04-20T10:00:00Z"}
{"type": "event", "_event": "v2_playbook_on_start", ...}
{"type": "event", "_event": "v2_playbook_on_play_start", ...}
...
{"type": "stats", "ok": 45, "changed": 12, "failed": 0, ...}
```

- **Implementation**:

```python
# artifacts/reader.py
from pathlib import Path
import json
from datetime import datetime
from typing import Optional

class ArtifactReader:
    """Read .aom artifact files."""
    
    @staticmethod
    def load_session(artifact_path: Path) -> 'RunState':
        """Load RunState from artifact file."""
        
        from ..state import RunState
        
        state = RunState()
        
        with open(artifact_path) as f:
            for line_num, line in enumerate(f, start=1):
                try:
                    entry = json.loads(line.strip())
                    entry_type = entry.get("type", "event")
                    
                    if entry_type == "metadata":
                        state.playbook = entry.get("playbook")
                        state.version = entry.get("version")
                        state.created = datetime.fromisoformat(entry.get("created"))
                    
                    elif entry_type == "event":
                        # Replay event through state machine
                        state.handle_event(entry)
                    
                    elif entry_type == "stats":
                        state.final_stats = entry
                    
                    else:
                        # Unknown entry type
                        print(f"Warning: Unknown entry type '{entry_type}' at line {line_num}")
                
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
        
        return state
    
    @staticmethod
    def get_session_metadata(artifact_path: Path) -> dict:
        """Get just the metadata (first line)."""
        with open(artifact_path) as f:
            first_line = f.readline()
            metadata = json.loads(first_line)
            return metadata
    
    @staticmethod
    def get_session_stats(artifact_path: Path) -> dict:
        """Get final stats (last line)."""
        with open(artifact_path) as f:
            # Read last line
            for line in f:
                pass
            stats = json.loads(line)
            return stats
```

**Usage in InspectScreen**:

```python
# screens/inspect.py
class InspectScreen(Screen):
    def __init__(self, session_id: str, artifact_path: Path):
        self.session_id = session_id
        self.artifact_path = artifact_path
        
        # Load state from artifact
        self.state = ArtifactReader.load_session(artifact_path)
        
        super().__init__()
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield TaskTree(self.state, readonly=True)
        # ...
```

### GQ4: How to integrate inspect TUI with CLI?

- **Context**: `aom inspect --tui <session>` should launch Textual TUI for browsing.

- **Implementation**:

```python
# cli.py
import click
from pathlib import Path
from .app import InspectApp

@click.group()
def main():
    """AOM - Ansible Output Monitor"""
    pass

@main.command()
@click.argument('session_id', required=False)
@click.option('--tui', is_flag=True, help='Open in TUI mode')
@click.option('--failed', is_flag=True, help='Show only failed tasks')
@click.option('--host', help='Filter by host')
@click.option('--tree', is_flag=True, help='Show task tree')
@click.option('--export', is_flag=True, help='Export as .aom artifact')
@click.pass_context
def inspect(ctx, session_id, tui, failed, host, tree, export):
    """Inspect saved sessions."""
    
    if session_id is None:
        # List all sessions
        sessions = list_sessions()
        if tui:
            # TUI mode: show selectable list
            app = SessionListApp(sessions)
            app.run()
        else:
            # CLI mode: print table
            print_sessions_table(sessions)
        return
    
    # Get artifact path
    artifact_path = get_artifact_path(session_id)
    
    if not artifact_path.exists():
        click.echo(f"Session not found: {session_id}", err=True)
        return 1
    
    if tui:
        # Launch Textual TUI
        app = InspectApp(session_id, artifact_path)
        app.run()
    else:
        # CLI output
        show_session_summary(session_id, artifact_path, failed, host, tree, export)


# app.py
class InspectApp(App):
    """Textual app for inspecting saved sessions."""
    
    CSS_PATH = "styles/inspect.tcss"
    
    def __init__(self, session_id: str, artifact_path: Path):
        self.session_id = session_id
        self.artifact_path = artifact_path
        super().__init__()
    
    def on_mount(self):
        # Load and display session
        self.push_screen(InspectScreen(self.session_id, self.artifact_path))


class SessionListApp(App):
    """TUI for selecting session from list."""
    
    def on_mount(self):
        self.push_screen(SessionListScreen())
```

---

## Summary of TUI Features Research

| Feature | Recommendation | Key Technology |
|---------|----------------|-----------------|
| **Inspect TUI** | Readonly Screen subclass reusing Tree/Log/Summary widgets | Textual `Screen`, `disabled` widgets |
| **Re-run Dialog (Shift+R)** | Hybrid: quick history + command line editor | Textual `ModalScreen`, `Input` validators |
| **Session Loading** | Replay events from JSONL into RunState | `ArtifactReader.load_session()` |
| **CLI Integration** | `--tui` flag launches Textual app | `click` + `App.run()` |

---

*Research completed 2026-04-20*

---

## Research: `aom inspect diff <session1> <session2>` Implementation (2026-04-20)

### Executive Summary

**Question**: How to implement `aom inspect diff <session1> <session2>` to compare two Ansible playbook runs with table view showing task-level and host-level diffs?

**Finding**: ARA (Ansible Run Analysis) does NOT provide built-in comparison functionality. No existing Ansible-specific diff tools were found. Implementation needs to be built from scratch, borrowing patterns from git diff tools and table libraries.

**Key Decisions**:
1. **Task matching**: Use `file:line` path + task name combination (most stable)
2. **Comparison scope**: Compare at task×host level (result granularity)
3. **Output**: Rich table with color-coded diff indicators
4. **Views**: `--task` (task-centric) and `--host` (host-centric) modes

---

### 1. Existing Tools Research

#### 1.1 ARA (Ansible Run Analysis)

**Repository**: https://github.com/ansible-community/ara

**What ARA Provides**:
- Recording of individual playbook executions to database
- Web interface for browsing results
- CLI for querying (`ara playbook list`, `ara host list`, etc.)
- REST API for programmatic access
- Host metrics aggregation across runs

**What ARA Does NOT Provide**:
- ❌ No comparison between different playbook runs
- ❌ No diff functionality
- ❌ No regression detection

**Evidence**: From ARA source code research:
- `models.py` defines `Playbook`, `Play`, `Task`, `Host`, `Result` models
- Each task has: `uuid`, `lineno`, `file`, `action`, `name`
- Each result has: `status`, `changed`, `duration`
- No `compare` or `diff` commands in CLI
- Issue #535 discusses diffs but for `--diff` file content, NOT run comparison

**Relevant ARA Data Model** ([models.py](https://github.com/ansible-community/ara/blob/master/ara/api/models.py)):

```python
class Task(Duration):
    """Data about Ansible tasks."""
    name = models.TextField(blank=True, null=True)
    uuid = Char32UUIDField(null=True)     # Task UUID from Ansible
    action = models.TextField()           # Module name (e.g., 'apt')
    lineno = models.IntegerField()         # Line number in file
    file = models.ForeignKey(File, ...)    # File reference (playbook or role)
    play = models.ForeignKey(Play, ...)
    playbook = models.ForeignKey(Playbook, ...)

class Result(Duration):
    """Data about Ansible results."""
    status = models.CharField(...)        # ok, failed, skipped, unreachable
    changed = models.BooleanField(...)
    host = models.ForeignKey(Host, ...)
    task = models.ForeignKey(Task, ...)
```

**TODO Item in ARA Contrib** ([contrib/mcp/reviews/2025-02-11/claude-opus-4.6.md](https://github.com/ansible-community/ara/blob/master/contrib/mcp/reviews/2025-02-11/claude-opus-4.6.md)):
> "`compare_playbooks` — Shows what changed between two runs – essential for regression analysis."
> "*Implementation*: Compare SHA1 hashes of files between two playbooks. If hashes differ, fetch content and generate a diff. Compare results by `(task_name, task_action, host_name)` to find status changes."

**Conclusion**: Comparison is a **desired but unimplemented** feature in ARA.

---

#### 1.2 Ansible-Specific Diff Tools

**Search Results**: None found.

- No CLI tools for comparing Ansible playbook runs
- `ansible-playbook --diff` compares file content within a single run (not across runs)
- `ansible-playbook --check` is for dry-run within a single run
- ARA metrics aggregate stats but don't compare specific runs

---

#### 1.3 General Diff Tools (Applicable Patterns)

**Terminal Diff Viewers**:

1. **Delta** ([dandavison/delta](https://github.com/dandavison/delta)):
   - Syntax-highlighted git diff pager
   - Side-by-side view
   - Word-level diff highlighting
   - Line numbers
   - Themes
   - **Applicable**: Rich table layout for comparison

2. **critique** ([remorses/critique](https://github.com/remorses/critique)):
   - Terminal UI for git diffs
   - Split view
   - Word-level diff
   - **Applicable**: TUI diff widget

3. **textual-diff-view** ([batrachianai/textual-diff-view](https://github.com/batrachianai/textual-diff-view)):
   - Textual widget for diffs
   - Unified and split view
   - Syntax highlighting
   - **Applicable**: Direct use in AOM's TUI mode

4. **diffnav** ([dlvhdr/diffnav](https://github.com/dlvhdr/diffnav)):
   - Git diff pager with file tree
   - GitHub-like interface
   - **Applicable**: File tree navigation pattern

5. **dv** ([darrenburns/dv](https://github.com/darrenburns/dv)):
   - Interactive diff explorer
   - Unified and split view
   - Command palette
   - **Applicable**: Interactive TUI patterns

**Table Libraries**:

1. **Rich** ([textualize/rich](https://github.com/textualize/rich)):
   - `Table` class for terminal tables
   - Column alignment, colors, borders
   - Auto-wrapping
   - **Best for**: CLI diff output in AOM

2. **cmd-table** ([Aarul5/cmd-table](https://github.com/Aarul5/cmd-table)):
   - Node.js table library
   - Built-in `Table.compare()` for side-by-side comparison
   - Diff highlighting
   - **Applicable pattern**: Compare function design

**Key Patterns for AOM**:
- Two-column layout (Run1 vs Run2)
- Color coding: Green (improved), Red (regressed), Yellow (changed), Dim (unchanged)
- Summary statistics at top
- Row-level filtering
- Collapsible groups

---

### 2. Task Matching Strategies

**Critical Problem**: How to reliably match the same task across two different playbook runs?

#### 2.1 Available Identifiers

**From JSONL Events** (`ansible.posix.jsonl` callback):

| Identifier | Example | Stability | Availability |
|------------|---------|-----------|--------------|
| `task.id` | `"abc123-def456-..."` | **UUID, very stable** | Every task event |
| `task.name` | `"Install nginx"` | **Weak** - names can change | Every task event |
| `task.path` | `"/playbook.yml:42"` | **Strong** - file:line is stable | Every task event |
| `task.action` | `"ansible.builtin.apt"` | **Weak** - module only | Every task event |
| Play context | `"Play 1"` | **Weak** - play names can change | From play events |
| Position index | Task #5 in play | **Weak** - fails if tasks reorder | Derived from sequence |

**From ARA Data Model**:

| Identifier | ARA Field | Stability |
|------------|-----------|-----------|
| Task UUID | `task.uuid` | Very stable |
| File + Line | `task.file.path` + `task.lineno` | **Very stable** |
| Task name | `task.name` | Weak |
| Module | `task.action` | Weak |

#### 2.2 Matching Strategy Comparison

**Strategy A: UUID-Based Matching** (Best)

```python
def match_by_uuid(task1, task2) -> bool:
    return task1.uuid == task2.uuid
```

**Pros**:
- ✅ Most reliable (UUIDs are globally unique)
- ✅ Handles task renames automatically
- ✅ Handles role updates (UUID stays same if task unchanged)

**Cons**:
- ❌ UUIDs only available at runtime (not from `--list-tasks`)
- ❌ Requires storing UUIDs during `aom` run
- ❌ Different Ansible versions may generate different UUIDs (unconfirmed)

**Suitability**: **Excellent for AOM** (since we record full JSONL events with UUIDs)

---

**Strategy B: File:Line Path Matching** (Strong)

```python
def match_by_path(task1, task2) -> bool:
    return task1.path == task2.path  # "playbook.yml:42"
```

**Pros**:
- ✅ Very stable (file:line rarely changes unless playbook edited)
- ✅ Available in JSONL events (`task.path`)
- ✅ Available in ARA (`task.file.path` + `task.lineno`)
- ✅ Works across different Ansible versions

**Cons**:
- ❌ Fails if playbook file moved/renamed
- ❌ Fails if tasks reordered (line numbers shift)
- ❌ Role tasks have paths in role directory (may differ across runs if role path changes)

**Suitability**: **Excellent fallback** when UUIDs unavailable

---

**Strategy C: Name + Play Context Matching** (Weak)

```python
def match_by_name(task1, task2) -> bool:
    # Normalize role prefixes: "nginx : Install" → "Install"
    name1 = normalize_task_name(task1.name)
    name2 = normalize_task_name(task2.name)
    
    # Also match play name
    return name1 == name2 and task1.play_name == task2.play_name
```

**Problem**: Task names are fragile
- Role prefixes format: `"role_name : Task Name"` (space-colon-space)
- Variable interpolation: `"Debug {{ var }}"` may change
- Name collisions: Multiple `"Install package"` tasks in different roles

**Suitability**: **Unreliable alone, use only as supplementary check**

---

**Strategy D: Position Index Matching** (Weakest)

```python
def match_by_position(task1, task2) -> bool:
    return task1.index_in_play == task2.index_in_play
```

**Pros**:
- ✅ Simple
- ✅ Works if playbook unchanged

**Cons**:
- ❌ Fails completely if tasks added/removed
- ❌ Fails if tasks reordered
- ❌ Fails if different plays have same task index

**Suitability**: **Not recommended**

---

#### 2.3 Recommended Matching Strategy: Hybrid UUID + Path

```python
class TaskMatcher:
    """Reliable task matching across runs using hybrid identifiers."""
    
    def match_tasks(self, tasks1: list[Task], tasks2: list[Task]) -> dict[str, Task]:
        """
        Match tasks from run1 to run2.
        
        Returns: {task1.id: task2} mapping
        """
        matches = {}
        
        # Phase 1: Try UUID matching (most reliable)
        by_uuid2 = {t.uuid: t for t in tasks2 if t.uuid}
        for task1 in tasks1:
            if task1.uuid and task1.uuid in by_uuid2:
                matches[task1.id] = by_uuid2[task1.uuid]
        
        # Phase 2: For unmatched tasks, try path matching
        unmatched1 = [t for t in tasks1 if t.id not in matches]
        by_path2 = {t.path: t for t in tasks2 if t.path}
        for task1 in unmatched1:
            if task1.path and task1.path in by_path2:
                # Verify path match makes sense (same play context?)
                matches[task1.id] = by_path2[task1.path]
        
        # Phase 3: For still unmatched, try name+play (warning-heavy)
        unmatched1 = [t for t in tasks1 if t.id not in matches]
        for task1 in unmatched1:
            # Try fuzzy name matching with warnings
            potential = self._fuzzy_name_match(task1, tasks2)
            if potential:
                self.logger.warning(
                    f"Task {task1.name} matched by fuzzy name (unreliable)"
                )
                matches[task1.id] = potential
        
        return matches
    
    def _fuzzy_name_match(self, task1: Task, tasks2: list[Task]) -> Task | None:
        """Attempt fuzzy name matching with play context."""
        normalized_name1 = self._normalize_name(task1.name)
        
        candidates = [
            t for t in tasks2
            if self._normalize_name(t.name) == normalized_name1
            and t.play_id == task1.play_id
        ]
        
        if len(candidates) == 1:
            return candidates[0]
        
        return None
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize task name for comparison."""
        # Strip role prefix: "role : task" → "task"
        if " : " in name:
            name = name.split(" : ", 1)[1]
        
        # Strip variable interpolation (approximate)
        # "Debug {{ var }}" → "Debug "
        import re
        name = re.sub(r'\{\{.*?\}\}', '', name)
        
        return name.strip()
```

---

### 3. Comparison Dimensions

#### 3.1 Task-Level Comparison (Per Task)

**Compare for each task (matched by UUID/path)**:

| Dimension | Run 1 Value | Run 2 Value | Diff Classification |
|-----------|--------------|-------------|---------------------|
| **Status** | `ok` | `failed` | **Regressed** 🔴 |
| Status | `failed` | `ok` | **Improved** 🟢 |
| Status | `ok` | `ok` | Unchanged ⚪ |
| Status | `ok` | `skipped` | Changed 🟡 |
| **Changed** | `false` | `true` | **Configuration drift** 🟡 |
| Changed | `true` | `false` | Idempotent now 🟢 |
| **Duration** | `2.3s` | `30.5s` | **Performance regression** 🔴 |
| Duration | `10s` | `2s` | Performance improvement 🟢 |
| **Host availability** | reachable | unreachable | **Host regressed** 🔴 |

#### 3.2 Host-Level Comparison (Per Host)

**Aggregate across all tasks for the same host**:

| Metric | Diff Class | Meaning |
|--------|------------|---------|
| Host unreachable (`0 → 1`) | 🔴 Regressed | Host went down |
| Host unreachable (`1 → 0`) | 🟢 Improved | Host recovered |
| Failed tasks increase | 🔴 Regressed | More failures |
| Changed tasks increase | 🟡 Attention | More configuration drift |
| Duration increase (2x+) | 🔴 Performance | Host slower |

#### 3.3 Playbook-Level Comparison

**Summary statistics across entire run**:

| Statistic | Example Diff |
|-----------|--------------|
| Total tasks | `45 → 47` (2 added) |
| Total duration | `5m23s → 8m12s` (slower) |
| Success rate | `100% → 95%` (regressed) |
| Hosts affected | `3 → 4` (one more host) |

---

### 4. Output Format: Table View

#### 4.1 Task-Centric View (`--task` flag)

```
aom inspect diff session1 session2 --task
```

**Display**: One row per task, showing status for all hosts

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Task Comparison: session1 vs session2                              ┃
┃ Summary: 3 regressed, 2 improved, 40 unchanged, 2 new, 1 removed  ┃
┠─────────────────────────────────────────────────────────────────────┨
┃ Task                        │ Run 1       │ Run 2       │ Status  ┃
┠─────────────────────────────┼─────────────┼─────────────┼─────────┨
┃ Install nginx               │             │             │         ┃
┃   web1:                     │ ● ok (2.3s) │ ● ok (2.5s) │ ⚪      ┃
┃   web2:                     │ ● ok (2.1s) │ ✖ failed    │ 🔴 REG  ┃
┃   db1:                      │ ○ skipped   │ ● ok (1.8s) │ 🟢 IMP  ┃
┠─────────────────────────────┼─────────────┼─────────────┼─────────┨
┃ Configure firewall           │             │             │         ┃
┃   web1:                     │ ◐ changed   │ ● ok        │ 🟡 CHG  ┃
┃   web2:                     │ ● ok        │ ◝ NEW      │ 🟡 NEW  ┃
┠─────────────────────────────┼─────────────┼─────────────┼─────────┨
┃ Restart nginx (removed)      │ ◜ all hosts │ -           │ 🔴 REM  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Legend: ●=ok, ✖=failed, ◐=changed, ○=skipped, ⊝=unreachable
        🔴=regressed, 🟢=improved, 🟡=attention, ⚪=unchanged
        REG=regressed, IMP=improved, CHG=changed, NEW=new, REM=removed
```

#### 4.2 Host-Centric View (`--host` flag)

```
aom inspect diff session1 session2 --host
```

**Display**: One row per host, showing aggregate stats per host

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Host Comparison: session1 vs session2                              ┃
┃ Summary: 1 host regressed (unreachable), 2 hosts improved         ┃
┠─────────────────────────────────────────────────────────────────────┨
┃ Host      │ Run 1           │ Run 2           │ Status            ┃
┠───────────┼─────────────────┼─────────────────┼───────────────────┨
┃ web1      │ ● 20 ok         │ ● 22 ok         │ ⚪ (+2 tasks)     ┃
┃           │ ◐  3 changed    │ ◐  1 changed    │ 🟢 less drift     ┃
┃           │ ✖  0 failed     │ ✖  0 failed     │                   ┃
┃           │ ⊝  0 unreachable│ ⊝  0 unreachable│                   ┃
┃           │ ⏱  5m23s        │ ⏱  5m45s        │ ⚪ (slower)       ┃
┠───────────┼─────────────────┼─────────────────┼───────────────────┨
┃ web2      │ ● 18 ok         │ ● 15 ok         │ 🔴 REGRESSED      ┃
┃           │ ✖  0 failed     │ ✖  3 failed     │ (3 new failures)  ┃
┃           │ ⊝  0 unreachable│ ⊝  1 unreachable│ (host down)       ┃
┃           │ ⏱  4m12s        │ ⏱  N/A         │                   ┃
┠───────────┼─────────────────┼─────────────────┼───────────────────┨
┃ db1       │ ● 10 ok         │ ● 10 ok         │ 🟢 IMPROVED       ┃
┃           │ ◐  5 changed    │ ◐  2 changed    │ (less drift)      ┃
┃           │ ✖  2 failed     │ ✖  0 failed     │ (fixed)           ┃
┃           │ ⏱  3m45s        │ ⏱  2m30s        │ (faster)          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

#### 4.3 Rich Table Implementation Pattern

**Based on Rich documentation** ([github.com/textualize/rich](https://github.com/textualize/rich)):

```python
from rich.console import Console
from rich.table import Table
from rich.text import Text

def create_diff_table(
    tasks1: list[TaskResult],
    tasks2: list[TaskResult],
    mode: str = "task"  # "task" or "host"
) -> Table:
    """Create diff comparison table."""
    
    # Calculate summary
    stats = calculate_diff_stats(tasks1, tasks2)
    
    # Create table
    table = Table(
        title=f"{'Task' if mode == 'task' else 'Host'} Comparison: session1 vs session2",
        show_lines=True,
        title_justify="left"
    )
    
    # Add columns
    table.add_column("Task" if mode == "task" else "Host", style="cyan", no_wrap=True)
    table.add_column("Run 1", justify="right")
    table.add_column("Run 2", justify="right")
    table.add_column("Status", justify="center", width=15)
    
    # Add summary row
    table.add_row(
        "[bold]Summary[/bold]",
        "",
        "",
        format_summary(stats)
    )
    table.add_section()
    
    # Add data rows
    for r1, r2 in match_and_compare(tasks1, tasks2, mode):
        diff = compute_diff(r1, r2)
        
        # Format values with icons and colors
        run1_val = format_task_result(r1)
        run2_val = format_task_result(r2)
        status_val = format_diff_status(diff)
        
        # Apply row style based on diff
        row_style = get_diff_style(diff)
        
        table.add_row(
            r1.name,
            run1_val,
            run2_val,
            status_val,
            style=row_style
        )
    
    return table

def format_task_result(result: TaskResult) -> Text:
    """Format a task result with icon and color."""
    icon_map = {
        "ok": ("●", "green"),
        "changed": ("◐", "yellow"),
        "failed": ("✖", "red bold"),
        "skipped": ("○", "dim"),
        "unreachable": ("⊝", "red dim"),
    }
    
    icon, color = icon_map.get(result.status, ("?", "white"))
    
    text = Text()
    text.append(icon, style=color)
    text.append(f" {result.status}")
    
    if result.duration:
        text.append(f" ({result.duration:.1f}s)", style="dim")
    
    return text

def format_diff_status(diff: DiffResult) -> Text:
    """Format diff status with color."""
    status_map = {
        "regressed": ("🔴 REGRESSED", "red bold"),
        "improved": ("🟢 IMPROVED", "green bold"),
        "changed": ("🟡 CHANGED", "yellow"),
        "new": ("🟡 NEW", "yellow"),
        "removed": ("🔴 REMOVED", "red dim"),
        "unchanged": ("⚪", "dim"),
    }
    
    label, style = status_map.get(diff.status, ("?", "white"))
    return Text(label, style=style)

def format_summary(stats: dict) -> Text:
    """Format summary statistics."""
    text = Text()
    
    if stats["regressed"] > 0:
        text.append(f"🔴 {stats['regressed']} regressed ", style="red bold")
    if stats["improved"] > 0:
        text.append(f"🟢 {stats['improved']} improved ", style="green bold")
    if stats["new"] > 0:
        text.append(f"🟡 {stats['new']} new ", style="yellow")
    if stats["removed"] > 0:
        text.append(f"🔴 {stats['removed']} removed ", style="red dim")
    
    return text
```

---

### 5. Edge Cases

#### 5.1 Different Playbooks

**Problem**: User tries to diff runs from different playbooks (e.g., `site.yml` vs `deploy.yml`)

**Detection**:
```python
def can_diff_sessions(session1, session2) -> tuple[bool, str]:
    """Check if sessions can be compared."""
    
    # Check playbook name
    if session1.playbook != session2.playbook:
        return False, f"Different playbooks: {session1.playbook} vs {session2.playbook}"
    
    # Check playbook content hash
    if session1.playbook_hash != session2.playbook_hash:
        return True, "WARNING: Playbook was modified between runs"
    
    # Check inventory
    hosts1 = set(session1.hosts.keys())
    hosts2 = set(session2.hosts.keys())
    if hosts1 != hosts2:
        return True, f"Different inventory: {hosts2 - hosts1} added, {hosts1 - hosts2} removed"
    
    return True, "OK"
```

**Handling**:
1. **Hard error**: Different playbook names (`site.yml` vs `other.yml`) → abort
2. **Warning**: Same playbook but modified → show warning, continue
3. **Proceed**: Different inventory → diff only matching hosts

#### 5.2 Inventory Changes

**Problem**: Hosts added or removed between runs

```
Run 1: web1, web2, db1
Run 2: web1, web2, db1, db2 (new host)
```

**Handling**:
- Diff hosts that exist in both runs
- Mark new hosts as "NEW" state
- Mark removed hosts as "REMOVED" state
- Update summary to show host changes

#### 5.3 Task Renames

**Problem**: Task renamed between runs
```
Run 1: "Install nginx"
Run 2: "Install nginx web server" (renamed task)
```

**Detection**:
- UUID matching: ✅ Still works (UUID unchanged)
- Path matching: ✅ Still works (file:line unchanged)
- Name matching: ❌ Fails

**Handling**:
- Hybrid matching will find match via UUID or path
- Show warning if matched by path: "Task name changed: X → Y"

#### 5.4 Task Reordering

**Problem**: Tasks moved to different positions in playbook
```
Run 1: Task A (line 10), Task B (line 20), Task C (line 30)
Run 2: Task C (line 10), Task A (line 20), Task B (line 30)
```

**Handling**:
- UUID matching: ✅ Still works
- Path matching: ✅ Still works (paths updated by Ansible)
- Position matching: ❌ Fails

#### 5.5 Same Task on Multiple Hosts

**Problem**: Single task runs on multiple hosts, each with different status
```
Task: "Install nginx"
  web1: ok
  web2: failed
  db1: skipped
```

**Diff representation**:
- In `--task` mode: Show each host as sub-row
- In `--host` mode: Aggregate (host-level view hides individual task nuances)

---

### 6. Recommended Implementation

#### 6.1 Data Models for Diff

```python
from dataclasses import dataclass
from enum import Enum

class DiffStatus(Enum):
    IMPROVED = "improved"
    REGRESSED = "regressed"
    CHANGED = "changed"
    NEW = "new"
    REMOVED = "removed"
    UNCHANGED = "unchanged"

@dataclass
class TaskDiff:
    """Diff for a single task (matched across runs)."""
    task_id: str
    task_name: str
    task_path: str  # file:line
    
    # Match metadata
    matched_by: str  # "uuid", "path", "name", "none"
    match_warning: str | None
    
    # Per-host diffs
    hosts: dict[str, "HostTaskDiff"]

@dataclass
class HostTaskDiff:
    """Diff for a task on a specific host."""
    host_name: str
    run1_status: str | None  # None if host didn't run this task
    run2_status: str | None
    run1_changed: bool | None
    run2_changed: bool | None
    run1_duration: float | None
    run2_duration: float | None
    diff_status: DiffStatus
    diff_reason: str  # "status changed", "duration changed", etc.

@dataclass
class SessionComparison:
    """Complete comparison between two sessions."""
    session1_id: str
    session2_id: str
    
    # Match validation
    can_diff: bool
    warning: str | None
    
    # Task diffs
    task_diffs: list[TaskDiff]
    
    # Host diffs (aggregated)
    host_diffs: dict[str, "HostDiff"]
    
    # Summary
    summary: "ComparisonSummary"

@dataclass
class ComparisonSummary:
    regressed: int
    improved: int
    changed: int
    new_tasks: int
    removed_tasks: int
    unchanged: int
    
    hosts_regressed: int
    hosts_improved: int
    hosts_new: int
    hosts_removed: int
```

#### 6.2 Core Diff Function

```python
def diff_sessions(session1: Session, session2: Session) -> SessionComparison:
    """
    Compare two playbook run sessions.
    
    Algorithm:
    1. Validate sessions can be compared (playbook match)
    2. Match tasks across runs (UUID → path → name)
    3. For each matched task, diff per-host results
    4. Identify new/removed tasks and hosts
    5. Aggregate statistics
    """
    
    # 1. Validate
    can_diff, warning = can_diff_sessions(session1, session2)
    
    if not can_diff:
        return SessionComparison(
            session1_id=session1.id,
            session2_id=session2.id,
            can_diff=False,
            warning=warning,
            task_diffs=[],
            host_diffs={},
            summary=ComparisonSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        )
    
    # 2. Match tasks
    task_matcher = TaskMatcher()
    task_mapping = task_matcher.match_tasks(
        session1.tasks,
        session2.tasks
    )
    
    # 3. Compute task diffs
    task_diffs = []
    for task1 in session1.tasks:
        task2 = task_mapping.get(task1.id)
        
        if task2:
            # Matched task: compute per-host diff
            host_diffs = compute_host_diffs(task1, task2)
            task_diff = TaskDiff(
                task_id=task1.id,
                task_name=task1.name,
                task_path=task1.path,
                matched_by=task_matcher.last_match_method,
                match_warning=task_matcher.last_match_warning,
                hosts=host_diffs
            )
            task_diffs.append(task_diff)
        else:
            # Removed task
            task_diff = TaskDiff(
                task_id=task1.id,
                task_name=task1.name,
                task_path=task1.path,
                matched_by="none",
                match_warning="Task removed in run 2",
                hosts={
                    host: HostTaskDiff(
                        host_name=host,
                        run1_status=task1.hosts[host].status,
                        run2_status=None,
                        diff_status=DiffStatus.REMOVED,
                        diff_reason="Task removed"
                    )
                    for host in task1.hosts
                }
            )
            task_diffs.append(task_diff)
    
    # 4. Find new tasks
    matched_task_ids = set(task_mapping.keys())
    for task2 in session2.tasks:
        if task2.id not in matched_task_ids:
            task_diff = TaskDiff(
                task_id=task2.id,
                task_name=task2.name,
                task_path=task2.path,
                matched_by="none",
                match_warning="Task new in run 2",
                hosts={
                    host: HostTaskDiff(
                        host_name=host,
                        run1_status=None,
                        run2_status=task2.hosts[host].status,
                        diff_status=DiffStatus.NEW,
                        diff_reason="Task added"
                    )
                    for host in task2.hosts
                }
            )
            task_diffs.append(task_diff)
    
    # 5. Aggregate statistics
    summary = compute_summary(task_diffs)
    
    return SessionComparison(
        session1_id=session1.id,
        session2_id=session2.id,
        can_diff=True,
        warning=warning,
        task_diffs=task_diffs,
        host_diffs=aggregate_by_host(task_diffs),
        summary=summary
    )
```

#### 6.3 CLI Command

```python
import click
from rich.console import Console

@click.group()
def cli():
    """AOM - Ansible Output Monitor."""
    pass

@cli.group()
def inspect():
    """Inspect session data."""
    pass

@inspect.command()
@click.argument("session1")
@click.argument("session2")
@click.option("--task", "mode", flag_value="task", default=True,
              help="Show task-centric diff (default)")
@click.option("--host", "mode", flag_value="host",
              help="Show host-centric diff")
@click.option("--failed", is_flag=True,
              help="Show only failed/regressed tasks")
@click.option("--json", is_flag=True,
              help="Output as JSON")
@click.pass_context
def diff(ctx, session1, session2, mode, failed, json):
    """
    Compare two playbook runs.
    
    Examples:
      aom inspect diff abc123 def456
      aom inspect diff abc123 def456 --host
      aom inspect diff abc123 def456 --failed --task
    """
    # Load sessions
    s1 = load_session(session1)
    s2 = load_session(session2)
    
    # Compute diff
    comparison = diff_sessions(s1, s2)
    
    if not comparison.can_diff:
        console = Console()
        console.print(f"[red]Error: {comparison.warning}[/red]")
        raise SystemExit(1)
    
    if comparison.warning:
        console = Console()
        console.print(f"[yellow]Warning: {comparison.warning}[/yellow]\n")
    
    # Output
    if json:
        output_json(comparison)
    elif mode == "task":
        table = create_task_diff_table(comparison, failed_only=failed)
        Console().print(table)
    else:  # mode == "host"
        table = create_host_diff_table(comparison, failed_only=failed)
        Console().print(table)
```

---

### 7. OPEN QUESTIONS for User Decision

#### OQ-DIFF-1: How strict should playbook matching be?

**Options**:
- A) **Strict**: Different playbook paths cannot be diffed (abort with error)
- B) **Lenient**: Allow diff even if playbook different, but warn
- C) **Hash-based**: Check content hash (allow diff if playbook modified but warn)

**Recommendation**: **Option A (Strict)** for MVP, because comparing different playbooks is confusing.

---

#### OQ-DIFF-2: How to handle tasks matched by different methods?

**Scenarios**:
1. Matched by UUID: Most reliable, no warning
2. Matched by path: Reliable, but playbook may have moved
3. Matched by name: Unreliable, should warn

**Options**:
- A) **Show warning on screen**: `[yellow]⚠ Matched by path (UUID unavailable)[/yellow]`
- B) **Log warning only**: Don't clutter output
- C) **Skip unreliable matches**: Only show high-confidence matches

**Recommendation**: **Option A (Show warning)** because transparency is important.

---

#### OQ-DIFF-3: Should we show tasks with no changes?

**Problem**: Large playbooks have many unchanged tasks, creating noise.

**Options**:
- A) **Show all**: All tasks, including unchanged
- B) **Hide unchanged by default**: Flag `--all` shows everything
- C) **Filter options**: `--changed`, `--failed`, `--regressed` flags

**Recommendation**: **Option B (Hide by default)** with `--all` flag to show everything.

**Default output**:
```
Summary: 3 regressed, 2 improved, 40 unchanged, 2 new, 1 removed
Showing: regressed, improved, new, removed (40 unchanged hidden)
Use --all to show all tasks
```

---

#### OQ-DIFF-4: Performance threshold for duration regression?

**Problem**: When is a duration change considered a "regression"?

**Example**: Task took 2.3s → 2.5s (is that a regression?)

**Options**:
- A) **Any increase**: 2.3s → 2.5s is regression (too sensitive)
- B) **Percentage threshold**: >20% increase is regression
- C) **Absolute + percentage**: >5s increase AND >10% increase
- D) **Manual classification**: Mark any duration change as "attention" (yellow)

**Recommendation**: **Option D (Manual classification)** for MVP. Mark duration changes as 🟡 "attention" (not regressed). Let user decide if it's a problem.

**Reasoning**: Duration depends on network, host load, etc. Hard to automatically classify.

---

#### OQ-DIFF-5: Should we support playbook code diffs?

**Problem**: This research focused on task/result diffs. What about showing the actual playbook code changes?

**Example**:
```
Run 1: playbook.yml line 42: "apt: name=nginx"
Run 2: playbook.yml line 42: "apt: name=nginx state=latest"
```

**Options**:
- A) **No code diffs**: Only compare results (task status, duration)
- B) **Basic code diffs**: Show unified diff of playbook file
- C) **Integrated code diffs**: For each regressed task, show what changed in playbook

**Recommendation**: **Option A (No code diffs)** for MVP. Code diffs add complexity (file storage, diff algorithm, role tracking).

**Future enhancement**: Use git diff integration if playbook is version-controlled.

---

### 8. Implementation Checklist

**Phase 1: Core Diff Logic** (P0)
- [ ] Session loading from `.aom` artifacts
- [ ] Task matching (UUID → path → name hierarchy)
- [ ] Per-host result comparison
- [ ] Diff classification (regressed/improved/changed/new/removed)
- [ ] Summary statistics

**Phase 2: Output** (P0)
- [ ] Rich table for `--task` view
- [ ] Rich table for `--host` view
- [ ] Summary line at top
- [ ] Color coding (red/green/yellow/dim)
- [ ] JSON output (`--json` flag)

**Phase 3: CLI Integration** (P0)
- [ ] `aom inspect diff <id1> <id2>` command
- [ ] `--task` / `--host` flag
- [ ] `--failed` / `--changed` filter flags
- [ ] `--all` flag to show unchanged
- [ ] Error handling for different playbooks

**Phase 4: Polish** (P1)
- [ ] Warning messages for path-based matches
- [ ] Warning for modified playbooks
- [ ] Host inventory change detection
- [ ] TUI mode for browsing diffs (interactive)
- [ ] Pipe-friendly output (non-TTY mode)

**Phase 5: Advanced** (P2)
- [ ] Duration regression detection (smart thresholds)
- [ ] Playbook code diffs (if version-controlled)
- [ ] Role-level aggregation
- [ ] Trend analysis across multiple runs
- [ ] Export to HTML/markdown report

---

### 9. References

**ARA (Ansible Run Analysis)**:
- Repository: https://github.com/ansible-community/ara
- Models: https://github.com/ansible-community/ara/blob/master/ara/api/models.py
- CLI: https://github.com/ansible-community/ara/tree/master/ara/cli
- Docs: https://ara.readthedocs.io/

**Diff Visualization**:
- Rich library: https://github.com/textualize/rich
- textual-diff-view: https://github.com/batrachianai/textual-diff-view
- Delta: https://github.com/dandavison/delta
- critique: https://github.com/remorses/critique

**Ansible Internals**:
- JSONL callback: https://github.com/ansible-collections/ansible.posix/blob/main/plugins/callback/jsonl.py
- Task UUIDs: Ansible internal documentation
- Task paths: `task.path` field in JSON events

**Python Patterns**:
- Rich Tables: https://rich.readthedocs.io/en/stable/tables.html
- Diff algorithms: difflib, patience diff

---

*Research completed 2026-04-20*

---

## Module Structure Research: Multiple Rendering Backends (2026-04-20)

### Executive Summary

**Question**: Best Python module structure for an app with TWO rendering backends (ANSI compact + Textual TUI) sharing a common core?

**Finding**: Use **Protocol-based abstraction** with **package-based structure** for both backends. The core defines interfaces via `typing.Protocol`, each renderer implements the protocol, and a factory instantiates the correct implementation based on CLI flags.

**Recommended Structure**:
```
aom/
├── __init__.py
├── cli.py                    # Entry point, factory selection
├── core/                     # Shared logic (UI-independent)
│   ├── __init__.py
│   ├── state.py              # State machine
│   ├── parser.py             # JSONL parser
│   ├── models.py             # Pydantic models
│   ├── session.py            # Session manager
│   ├── artifact.py           # Artifact writer
│   └── config.py             # Config
├── renderer/                 # Rendering abstraction
│   ├── __init__.py
│   └── protocol.py           # Renderer Protocol definition
├── compact/                  # ANSI compact renderer
│   ├── __init__.py
│   ├── renderer.py           # CompactRenderer implementation
│   ├── display.py            # Rich Live rendering
│   ├── status_panel.py       # Status panel
│   ├── password.py           # Password pass-through
│   └── nontty.py             # Non-TTY fallback
└── tui/                      # Textual TUI renderer  
    ├── __init__.py
    ├── app.py                # AOMApp (Textual App)
    ├── screens/
    │   ├── __init__.py
    │   ├── main.py           # Main screen
    │   ├── help.py           # Help overlay
    │   ├── search.py         # Search overlay
    │   └── settings.py       # Settings screen
    ├── widgets/
    │   ├── __init__.py
    │   ├── tree.py           # Play/Task tree
    │   ├── log.py            # Rich log panel
    │   ├── summary.py        # Summary panel
    │   ├── status_bar.py     # Status bar
    │   └── password_modal.py # Password input modal
    └── themes.py             # Theme definitions
```

---

### DQ1: How to cleanly separate the shared core from both renderers?

**Answer**: Use **Protocol-based abstraction** with **explicit dependency boundaries**.

**Evidence** (from IBM mcp-cli architecture):

From [mcp-cli architecture.md](https://github.com/IBM/mcp-cli/blob/main/architecture.md):

```markdown
## 5. Core / UI Separation

Logic that is UI-independent must not import from `display/`, `interactive/`, or `commands/`. 
Core modules use `logging` only — never `chuk_term.ui.output`.

**Core modules** (use `logging` only):
- `chat/` — conversation, tool processing, context, session management
- `config/` — defaults, configuration loading, server models
- `tools/` — tool management, execution, filtering

**UI modules** (may use `chuk_term.ui.output`):
- `display/` — streaming display, rendering
- `interactive/` — terminal shell, prompt sessions
- `commands/` — CLI command handlers

**Future goal:** core modules extractable into a standalone `mcp-cli-core` package.
```

**Implementation Pattern**:

```python
# aom/core/state.py - Core module (UI-independent)
import logging
from typing import Protocol

logger = logging.getLogger(__name__)

class StateProtocol(Protocol):
    """Protocol for state observers (renderers)."""
    def on_state_change(self, event: Event) -> None: ...

class RunState:
    """Core state - no UI dependencies."""
    
    def __init__(self):
        self.plays: dict[str, Play] = {}
        self.hosts: dict[str, HostStats] = {}
        self._observers: list[StateProtocol] = []
    
    def add_observer(self, observer: StateProtocol) -> None:
        self._observers.append(observer)
    
    def handle_event(self, event: Event) -> None:
        # Update state
        # ...
        # Notify observers (renderers)
        for observer in self._observers:
            observer.on_state_change(event)


# aom/compact/renderer.py - UI module (imports core only)
from aom.core.state import RunState
from aom.renderer.protocol import Renderer

class CompactRenderer:
    """ANSI compact renderer - implements Renderer Protocol."""
    
    def __init__(self, state: RunState):
        self.state = state
        state.add_observer(self)
    
    def on_state_change(self, event: Event) -> None:
        # Update display
        pass


# aom/tui/app.py - UI module (imports core only)
from textual.app import App
from aom.core.state import RunState

class AOMApp(App):
    """Textual TUI - implements Renderer Protocol."""
    
    def __init__(self, state: RunState):
        super().__init__()
        self.state = state
        state.add_observer(self)
```

**Key Principles**:

1. **Core imports nothing from UI**: `aom/core/` never imports from `aom/compact/` or `aom/tui/`
2. **UI imports core**: Both renderers import from `aom/core/`
3. **Protocol in shared location**: `aom/renderer/protocol.py` defines the interface
4. **Testability**: Core can be tested without UI (mock/protocol)

---

### DQ2: Python project examples with multiple rendering backends?

**Finding**: Limited direct examples found, but pattern is similar to **adapter/backends** in other domains.

**Evidence** (from GitHub searches):

1. **Backend abstraction pattern** (multiple examples):

```python
# From docling-project/docling (document processing backends)
class AbstractDocumentBackend(ABC):
    @abstractmethod
    def __init__(self, in_doc: "InputDocument", path_or_stream: Union[BytesIO, Path]):
        ...

# From letta-ai/letta (storage backends)
class ProviderTraceBackendClient(ABC):
    """Abstract base class for provider trace storage backends."""
    @abstractmethod
    async def create_async(self, ...):
        pass
```

2. **Textual apps with Rich fallback**:

No direct examples found of "Textual + Rich dual rendering", but **Textual itself** uses Rich internally:

```python
# Textual uses Rich for rendering under the hood
from rich.text import Text
from rich.style import Style
```

3. **Multiple UI modes** (from mcp-cli):

From mcp-cli architecture:
```markdown
**Core modules** (use `logging` only):
- chat/, config/, tools/, model_management/, memory/, auth/, context/

**UI modules** (may use `chuk_term.ui.output`):
- display/, interactive/, commands/, adapters/, chat/ui_manager.py
```

**Pattern Synthesis**:

```
aom/
├── core/           # Shared logic (NO UI dependencies)
│   ├── state.py
│   ├── parser.py
│   └── ...
├── renderer/       # Interface definition
│   └── protocol.py
├── compact/        # Backend 1 (ANSI)
│   └── renderer.py
└── tui/            # Backend 2 (Textual)
    └── app.py
```

This matches the **"ports and adapters"** architecture from hexagonal architecture.

---

### DQ3: Single-module vs package - when to split?

**Answer**: Split when **>500 lines** OR **>3 distinct responsibilities**.

**Evidence** (from research):

From [engineersofai.com](https://engineersofai.com/docs/python/python-foundation/clean-code-and-engineering-standards/project-structure):

```markdown
## When to Split Into Sub-packages

A module has grown too large when:
- It exceeds roughly **500 lines**
- It has **more than 3 distinct responsibilities**

Convert a module to a sub-package by turning it into a directory:

The key: **callers do not need to change**. Code that imports from `module.py`
continues to import from `module/__init__.py`.

### Q4: When should you split a module into a sub-package?

Answer: The practical triggers are:
- The module exceeds roughly 500 lines
- It has three or more distinct responsibilities
- You find yourself adding section-separator comments inside a single file

When these conditions appear, the module is doing too much.
```

**Application to AOM**:

| Component | Est. Lines | Responsibilities | Structure |
|-----------|------------|------------------|-----------|
| **Core state** | ~300 | State machine, event handling | Single module (`core/state.py`) |
| **Core parser** | ~200 | JSONL parsing | Single module (`core/parser.py`) |
| **Core models** | ~400 | Pydantic models | Single module (`core/models.py`) |
| **Compact renderer** | ~400 | Rendering, status, password | **Package** (5 files × ~80 lines each) |
| **TUI renderer** | ~2000+ | Multiple widgets, screens | **Package** (10+ files × ~200 lines each) |

**Recommendation**:

- **Single module** for: core components (<500 lines, focused responsibility)
- **Package** for: compact renderer (5 files for clarity), **tui renderer** (10+ files for manageability)

**Split criteria**:
- **Compact**: 400 lines but 5 responsibilities → **Split into package**
- **TUI**: 2000+ lines, 10 responsibilities → **Split into package**

---

### DQ4: Should both renderers implement a common Protocol/ABC?

**Answer**: **YES - use `typing.Protocol` (not ABC)** for interface definition.

**Evidence** (from PEP 544 and real-world usage):

From [PEP 544](https://peps.python.org/pep-0544/):

```markdown
Protocols provide **structural subtyping** (static duck typing).
Objects that have the right methods match the protocol without inheritance.

This is significantly more flexible and more "Pythonic" when you care about 
behavior rather than inheritance.
```

From [mcp-cli architecture.md](https://github.com/IBM/mcp-cli/blob/main/architecture.md):

```markdown
## 9. Protocol-Based Interfaces

Use `Protocol` (structural subtyping) for component boundaries — not ABC inheritance.

**Rules:**
- Core interfaces defined as `@runtime_checkable` Protocols
- Protocols specify the minimal surface area needed by consumers
- Concrete classes satisfy protocols implicitly — no explicit `implements` declaration
- Tests use simple dummy classes that satisfy the protocol without subclassing
```

**Protocol vs ABC Comparison**:

| Aspect | Protocol | ABC |
|--------|----------|-----|
| **Subtyping** | Structural (duck typing) | Nominal (inheritance) |
| **Flexibility** | High (any matching class works) | Low (must inherit) |
| **Testing** | Easy (mock just needed methods) | Harder (must subclass) |
| **Type checking** | Static checkers support | Static checkers support |
| **Runtime check** | `isinstance()` with `@runtime_checkable` | `isinstance()` always |
| **Explicit contract** | No declare needed | Must inherit |

**Recommended Protocol**:

```python
# aom/renderer/protocol.py
from typing import Protocol, runtime_checkable
from aom.core.models import Event, RunState

@runtime_checkable
class Renderer(Protocol):
    """
    Protocol for rendering backends.
    
    Both CompactRenderer and AOMApp (TUI) must satisfy this protocol.
    """
    
    def render_status(self, state: RunState) -> None:
        """Render current status."""
        ...
    
    def render_log_line(self, line: str, event: Event) -> None:
        """Render a log line from ansible-playbook."""
        ...
    
    def handle_password(self, prompt: str) -> str:
        """Handle password prompt interactively."""
        ...
    
    def handle_completion(self, state: RunState) -> None:
        """Handle playbook completion."""
        ...
    
    def start(self) -> None:
        """Initialize renderer."""
        ...
    
    def stop(self) -> None:
        """Cleanup renderer."""
        ...


# aom/compact/renderer.py
class CompactRenderer:
    """
    ANSI compact renderer - satisfies Renderer Protocol.
    
    No explicit inheritance - just implement the methods.
    """
    
    def __init__(self, state: RunState, console: Console):
        self.state = state
        self.console = console
    
    def render_status(self, state: RunState) -> None:
        # Rich ANSI rendering with cursor positioning
        pass
    
    def render_log_line(self, line: str, event: Event) -> None:
        self.console.print(line)
    
    def handle_password(self, prompt: str) -> str:
        # Use getpass inline (no TUI)
        import getpass
        return getpass.getpass(prompt)
    
    # ... other methods


# aom/tui/app.py
from textual.app import App

class AOMApp(App):
    """
    Textual TUI - also satisfies Renderer Protocol.
    
    Note: inherits from App, not from Renderer.
    Protocol satisfaction is structural, not nominal.
    """
    
    def render_status(self, state: RunState) -> None:
        # Update Textual widgets
        pass
    
    def render_log_line(self, line: str, event: Event) -> None:
        # Append to RichLog widget
        pass
    
    def handle_password(self, prompt: str) -> str:
        # Show password modal
        pass
    
    # ... other methods
```

**Testing benefit**:

```python
# tests/test_renderer.py
def test_renderer_protocol():
    """Test that renderer satisfies protocol."""
    
    # Simple mock for testing
    class MockRenderer:
        def render_status(self, state): pass
        def render_log_line(self, line, event): pass
        def handle_password(self, prompt): return "test"
        def handle_completion(self, state): pass
        def start(self): pass
        def stop(self): pass
    
    mock = MockRenderer()
    assert isinstance(mock, Renderer)  # Runtime check passes
    
    # No need to subclass ABC or implement all methods
```

**Why Protocol over ABC**:

1. **No inheritance constraint**: `AOMApp` already inherits from `App`, can't multiply inherit from ABC
2. **Duck typing**: Focus on behavior, not hierarchy
3. **Testing**: Easy to create mocks (just implement needed methods)
4. **Type safety**: MyPy/Pyright check protocol satisfaction statically

---

### DQ5: Dependency injection - factory pattern for renderer selection?

**Answer**: **YES - use factory function** to instantiate correct renderer based on CLI args.

**Evidence** (from dependency injection patterns):

From [softwareengineering.stackexchange.com](https://softwareengineering.stackexchange.com/questions/387896/factory-that-returns-multiple-implementations-of-the-same-interface):

```markdown
A "factory" that returns multiple implementations of the same interface:

**Named dependencies and factories are not the right way to handle this.**
Instead of asking for two different implementations, ask for what you need:
`IEnumerable<Interface>` (all implementations).

Use a single factory for all validators. The single factory can expose methods
for retrieving validators that are appropriate.
```

**Factory Pattern**:

```python
# aom/renderer/factory.py
from typing import Literal, Union
from aom.core.state import RunState
from aom.renderer.protocol import Renderer
from aom.compact.renderer import CompactRenderer
from aom.tui.app import AOMApp

RendererMode = Literal["compact", "tui"]

def create_renderer(
    mode: RendererMode,
    state: RunState,
    **kwargs
) -> Renderer:
    """
    Factory function to create renderer.
    
    Args:
        mode: "compact" for ANSI, "tui" for Textual
        state: RunState instance (shared by both renderers)
        **kwargs: Additional renderer-specific options
    
    Returns:
        Renderer instance (satisfies Renderer Protocol)
    
    Example:
        renderer = create_renderer("compact", state)
        renderer.start()
    """
    if mode == "compact":
        from rich.console import Console
        console = kwargs.get("console", Console())
        return CompactRenderer(state, console)
    
    elif mode == "tui":
        return AOMApp(state)
    
    else:
        raise ValueError(f"Unknown mode: {mode}")


# aom/cli.py
import click
from aom.core.state import RunState
from aom.renderer.factory import create_renderer

@click.command()
@click.option('--tui', is_flag=True, help='Use full TUI mode')
@click.option('--compact', is_flag=True, help='Use compact mode (default)')
@click.pass_context
def run(ctx, tui, compact):
    """Run ansible-playbook with monitoring."""
    
    # Create shared state
    state = RunState()
    
    # Determine mode (default: compact)
    mode = "tui" if tui else "compact"
    
    # Create renderer via factory
    renderer = create_renderer(mode, state)
    
    # Start renderer
    renderer.start()
    
    try:
        # Stream ansible-playbook output
        for event in stream_ansible():
            state.handle_event(event)
            renderer.render_log_line(event.raw_line, event)
            renderer.render_status(state)
        
        # Handle completion
        renderer.handle_completion(state)
    
    finally:
        renderer.stop()
```

**Alternative: Class Factory**:

```python
# aom/renderer/factory.py
from typing import Type

class RendererFactory:
    """Factory class for creating renderers."""
    
    _registry: dict[str, Type[Renderer]] = {}
    
    @classmethod
    def register(cls, mode: str, renderer_class: Type[Renderer]) -> None:
        """Register a renderer class for a mode."""
        cls._registry[mode] = renderer_class
    
    @classmethod
    def create(cls, mode: str, state: RunState, **kwargs) -> Renderer:
        """Create a renderer instance."""
        renderer_class = cls._registry.get(mode)
        if not renderer_class:
            raise ValueError(f"Unknown mode: {mode}")
        return renderer_class(state, **kwargs)


# Register renderers
RendererFactory.register("compact", CompactRenderer)
RendererFactory.register("tui", AOMApp)


# Usage
renderer = RendererFactory.create("compact", state)
```

**Why factory pattern**:

1. **Single decision point**: Mode selection in one place
2. **Testability**: Easy to mock renderer in tests
3. **Extensibility**: Easy to add new modes (e.g., "web", "headless")
4. **Loose coupling**: CLI doesn't know about specific renderer classes

---

### DQ6: Specific structure recommendation for AOM?

**Recommendation**: **Package structure** for both renderers, with clear responsibility boundaries.

**Recommended Module Layout**:

```
aom/
├── __init__.py
├── __main__.py               # Entry point: `python -m aom`
├── cli.py                    # Click CLI commands
│
├── core/                     # Core (2800 lines total)
│   ├── __init__.py
│   ├── state.py              # State machine (~300 lines)
│   ├── parser.py             # JSONL parser (~200 lines)
│   ├── models.py             # Pydantic models (~400 lines)
│   ├── session.py            # Session manager (~300 lines)
│   ├── artifact.py           # Artifact writer (~200 lines)
│   ├── config.py             # Config (~100 lines)
│   └── events.py             # Event types (~200 lines)
│
├── renderer/                 # Interface layer
│   ├── __init__.py
│   ├── protocol.py           # Renderer Protocol (~50 lines)
│   └── factory.py            # Factory function (~50 lines)
│
├── compact/                  # Compact renderer (400 lines split into 5 files)
│   ├── __init__.py           # Exports CompactRenderer
│   ├── renderer.py           # CompactRenderer class (~100 lines)
│   ├── display.py            # Rich Live rendering (~80 lines)
│   ├── status_panel.py       # Status panel (~80 lines)
│   ├── password.py           # Password pass-through (~40 lines)
│   └── nontty.py             # Non-TTY fallback (~40 lines)
│
└── tui/                      # TUI renderer (2000+ lines split into packages)
    ├── __init__.py           # Exports AOMApp
    ├── app.py                # AOMApp class (~300 lines)
    │
    ├── screens/              # Screen modules (~600 lines total)
    │   ├── __init__.py
    │   ├── main.py            # Main screen (~200 lines)
    │   ├── help.py            # Help overlay (~100 lines)
    │   ├── search.py          # Search overlay (~150 lines)
    │   └── settings.py       # Settings screen (~150 lines)
    │
    ├── widgets/              # Widget modules (~900 lines total)
    │   ├── __init__.py
    │   ├── tree.py            # Play/Task Tree widget (~200 lines)
    │   ├── log.py             # RichLog panel (~150 lines)
    │   ├── summary.py         # Summary panel (~100 lines)
    │   ├── status_bar.py      # Status bar widget (~100 lines)
    │   └── password_modal.py  # Password input modal (~100 lines)
    │
    └── themes.py             # Theme definitions (~200 lines)
```

**Why this structure**:

1. **Core as packages**: Even though `compact` is only 400 lines, it has 5 distinct responsibilities
2. **TUI as package**: 2000+ lines, 10+ responsibilities, needs organization
3. **Screens package**: Each screen is a self-contained module
4. **Widgets package**: Each widget is a self-contained module
5. **Protocol + Factory**: Shared interface in `renderer/`

**Import Patterns**:

```python
# Core imports nothing from UI
# aom/core/state.py
import logging
from typing import Protocol
from .models import Event, Play, HostStats
# NO imports from aom.compact or aom.tui

# Compact imports core + protocol
# aom/compact/renderer.py
from rich.console import Console
from aom.core.state import RunState
from aom.renderer.protocol import Renderer

# TUI imports core + protocol
# aom/tui/app.py
from textual.app import App
from aom.core.state import RunState
from aom.renderer.protocol import Renderer

# CLI imports everything
# aom/cli.py
import click
from aom.core.state import RunState
from aom.renderer.factory import create_renderer
```

**Test Structure**:

```
tests/
├── core/
│   ├── test_state.py
│   ├── test_parser.py
│   └── test_models.py
├── compact/
│   └── test_renderer.py
├── tui/
│   └── test_app.py
└── conftest.py               # Fixtures
```

---

## Summary: Module Structure Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Core/UI separation** | Core imports nothing from UI | Testability, reusability |
| **Python examples** | Backend/adapter pattern | No direct examples, but pattern established |
| **Single vs package** | Split at 500 lines / 3 responsibilities | Practical threshold from research |
| **Protocol vs ABC** | **Protocol** | Structural typing, no inheritance constraint |
| **Dependency injection** | **Factory function** | Single decision point, testable |
| **Specific structure** | **Both renderers as packages** | Clarity even for compact renderer |

**Implementation Effort Estimate**: 
- **Core**: Medium (1-2 days) - state machine, parser, models
- **Compact renderer**: Short (4-6 hours) - 5 small files
- **TUI renderer**: Large (2-3 days) - 10+ files, screens, widgets
- **Protocol + Factory**: Quick (<1 hour) - simple interface

**Total**: **3-5 days** for complete implementation.

---

*Research completed 2026-04-20*

---

## TERMINAL COMPATIBILITY AND SIGNAL HANDLING RESEARCH (2026-04-20)

### OVERVIEW

This research covers terminal compatibility requirements and signal handling for AOM's two rendering modes:
1. **Compact mode**: Uses Rich Live + blessed for terminal manipulation
2. **TUI mode**: Uses Textual framework for full-screen interface

---

## 1. TERMINAL COMPATIBILITY

### 1.1 Textual (TUI Mode)

**Official Requirements** (from Textual documentation):

**Source**: [Textual Getting Started](https://textual.textualize.io/getting_started/)

- **Python**: 3.9 or later (Python 3.14+ supported as of v7.3.0)
- **OS**: Linux, macOS, Windows, "and probably any OS where Python also runs"

**Terminal Recommendations**:

| Terminal | Support Level | Notes |
|----------|---------------|-------|
| **iTerm2** (macOS) | ✅ Recommended | Excellent color support |
| **Ghostty** (macOS/Linux) | ✅ Recommended | Modern, fast |
| **Kitty** (Linux/macOS) | ✅ Recommended | Full feature support |
| **WezTerm** (cross-platform) | ✅ Recommended | Works well |
| **Windows Terminal** (Windows) | ✅ Recommended | "Runs Textual apps beautifully" |
| **macOS Terminal.app** | ⚠️ Limited | 256 colors only, slower |
| **GNOME Terminal** (Linux) | ✅ Works | Standard Linux terminal |
| **Linux Console** | ✅ Works | Needs configuration (see linux-console.md) |

**Key Evidence** ([Textual FAQ](https://textual.textualize.io/FAQ/)):

> "macOS: The default terminal app is limited to 256 colors. We recommend installing a newer terminal such as iTerm2, Ghostty, Kitty, or WezTerm."

**Modern TUI Baseline** (from [Terminfo.dev](https://www.terminfo.dev/framework/textual)):

Textual works best with these terminal features:
- **TrueColor** (24-bit color): For CSS-like color system
- **Mouse tracking**: For interactive widgets
- **Bracketed paste**: For text input widgets
- **Hyperlinks**: Optional, when available

**Evidence**: "Textual requires the Modern TUI baseline— 4 of 13 tested terminals are fully compatible. Compatible: Ghostty, Kitty, iTerm2, cmux."

---

### 1.2 Rich (Compact Mode)

**Official Requirements** (from Rich documentation):

**Source**: [Rich Introduction](https://rich.readthedocs.io/en/stable/introduction.html)

- **Python**: 3.8.0 or later (3.14+ supported as of v14.2.0)
- **OS**: macOS, Linux, Windows
- **Windows**: Supports both cmd.exe and Windows Terminal

**Terminal Support**:

| Feature | Support |
|---------|---------|
| **Colors** | Auto-detects (ANSI 16, 256, or truecolor/24-bit) |
| **Styles** | Auto-stripped when piped |
| **Non-TTY** | Gracefully degrades to plain text |
| **Jupyter** | Works in notebooks |

**Environment Variables** ([Rich Console Docs](https://rich.readthedocs.io/en/stable/console.html)):

- `TERM=dumb` or `TERM=unknown`: Disables colors/style
- `NO_COLOR`: Removes colors but preserves styles (bold, italic, etc.)
- `TTY_COMPATIBLE=1`: Force TTY support
- `TTY_COMPATIBLE=0`: Force non-TTY mode
- `TTY_INTERACTIVE`: Force interactive mode on/off (v14.0.0+)
- `UNICODE_VERSION`: Set Unicode version for width calculations (v14.3.3+)

**Graceful Degradation**:

```python
# From Rich documentation
console = Console()

# Auto-detect capabilities
if console.is_terminal:
    # Use full formatting
    console.print("[bold red]Error[/bold red]")
else:
    # Plain text when piped
    console.print("Error")  # Strips ANSI
```

---

### 1.3 blessed (Compact Mode)

**Official Requirements** (from blessed documentation):

**Source**: [blessed PyPI](https://pypi.org/project/blessed/)

- **Python**: 3.7+ (Windows support added Dec 2019)
- **OS**: Windows, macOS, Linux, BSD
- **Dependencies**: `wcwidth`, `six`

**Key Features**:

| Feature | Support |
|---------|---------|
| **Terminfo** | Uses terminfo(5) for capabilities |
| **Colors** | 24-bit color support (Terminal.color_rgb()) |
| **Non-TTY** | Intelligent handling when piped |
| **Resize** | SIGWINCH support + in-band resize notifications (DEC mode 2048) |
| **Unicode** | Proper width handling via wcwidth |

**Unicode Width Handling**:

blessed uses `wcwidth` for proper Unicode character width calculation. This is critical for East Asian characters and emoji.

**Evidence** ([wcwidth docs](https://wcwidth.readthedocs.io/en/latest/intro.html)):

```python
import wcwidth

# Width of Unicode characters
wcwidth.wcwidth('a')      # 1 (narrow)
wcwidth.wcwidth('字')     # 2 (wide)
wcwidth.wcwidth('😊')    # 2 (wide emoji)
wcwidth.wcwidth('\u200b') # 0 (zero-width space)
```

**blessed's Terminal Detection** ([blessed Terminal API](https://blessed.readthedocs.io/en/stable/api/terminal.html)):

```python
from blessed import Terminal

term = Terminal()

# Check capabilities
if term.does_inband_resize(timeout=0.5):
    # Modern: Use in-band resize (DEC mode 2048)
    with term.notify_on_resize():
        # resize events via term.inkey()
        pass
else:
    # Fallback: Use SIGWINCH (Unix only)
    if sys.platform != 'win32':
        signal.signal(signal.SIGWINCH, on_resize)
```

---

### 1.4 Terminal Support Matrix for AOM

| Terminal | Compact Mode (Rich/blessed) | TUI Mode (Textual) | Notes |
|----------|------------------------------|--------------------| -------|
| **xterm** | ✅ Works | ✅ Works | Basic but functional |
| **xterm-256color** | ✅ Works | ✅ Works | Better colors |
| **kitty** | ✅ Works | ✅ Works | Full support, fast |
| **alacritty** | ✅ Works | ✅ Works | GPU-accelerated |
| **gnome-terminal** | ✅ Works | ✅ Works | Standard Linux |
| **iTerm2** | ✅ Works | ✅ Recommended | Excellent for macOS |
| **Windows Terminal** | ✅ Works | ✅ Recommended | Best for Windows |
| **macOS Terminal.app** | ✅ Works | ⚠️ Limited | 256 colors only |
| **screen** | ⚠️ Limited | ⚠️ Limited | SIGWINCH issues, no truecolor |
| **tmux** | ⚠️ Limited | ⚠️ Limited | Pass-through issues |
| **SSH** | ✅ Works | ✅ Works | Latency considerations |

**Compatibility Notes**:

#### tmux/screen Issues

**Source**: [Terminfo.dev - Multiplexers](https://terminfo.dev/multiplexers)

> "A multiplexer must understand an escape sequence to relay it correctly... This is why an application might work perfectly in Ghostty but break inside tmux."

**Known Issues**:
1. **TrueColor degradation**: tmux may not pass through 24-bit color correctly
2. **Mouse mode issues**: SGR mouse sequences may not pass through
3. **Kitty keyboard protocol**: Not passed through by tmux/screen
4. **SIGWINCH timing**: Race conditions in nested terminals

**Evidence** ([tmux Issue #2721](https://github.com/tmux/tmux/issues/2721)):
> "Mouse events (scrolling, in particular) are passed to the outermost tmux only, whereas previously they would be passed..."

**Recommendation**: For AOM in tmux/screen:
- Use `TERM=tmux-256color` or `TERM=screen-256color` (not `xterm-256color`)
- Test with `TERM=screen` if issues occur (some terminals support it better)
- Disable mouse if not working: `aom --no-mouse site.yml`

---

## 2. MINIMUM TERMINAL REQUIREMENTS

### 2.1 TERM Environment Variable

**Required**: A valid terminfo entry must exist.

**Common Values**:

| TERM Value | Colors | Unicode | Mouse | Notes |
|------------|--------|---------|-------|-------|
| `xterm` | 16 | Basic | Basic | Minimal |
| `xterm-256color` | 256 | Good | Good | Common |
| `xterm-truecolor` | 16M | Full | Full | Modern |
| `tmux-256color` | 256 | Good | Partial | Inside tmux |
| `screen-256color` | 256 | Good | Partial | Inside screen |
| `linux` | 8 | Basic | No | Linux console |

### 2.2 Color Requirements

**Compact Mode** (Rich):
- **Minimum**: 16 ANSI colors (works in basic terminals)
- **Recommended**: 256 colors (for better status indicators)
- **Optimal**: TrueColor (for CSS-like styling)

**TUI Mode** (Textual):
- **Minimum**: 256 colors
- **Recommended**: TrueColor/CSS color system

**Detection**:

```python
# Rich auto-detects
from rich.console import Console
console = Console()
print(f"Colors: {console.color_system}")  # 'standard', '256', or 'truecolor'
```

### 2.3 Unicode Requirements

**Required**: Terminal must support:
- **Box drawing characters**: U+2500-U+257F (┃━┏┗┣┫)
- **Geometric shapes**: U+25CF (●), U+25CB (○)
- **Checkmarks/crosses**: U+2714 (✔), U+2718 (✘)
- **Arrows**: U+2191 (↑), U+2193 (↓)
- **Clock**: U+23F1 (⏱)

**Fallback**: If Unicode unavailable, use ASCII equivalents:
- Box drawing: `|` `-` `+`
- Status: `[OK]` `[FAIL]` `[RUN]`

**blessed handles width correctly**:

```python
from blessed import Terminal

term = Terminal()
# Calculate display width (accounts for wide characters)
width = len(term.strip_seqs(text))  # Strips ANSI, counts visible width
```

### 2.4 Mouse Support

**Compact Mode**:
- **Not required**: Compact mode doesn't need mouse
- Status panel is non-interactive

**TUI Mode** (Textual):
- **Required**: For interactive widgets
- **Detection**: Rich/Textual auto-detect mouse capability

---

## 3. SIGNAL HANDLING

### 3.1 SIGINT (Ctrl+C)

**Already specified**: AOM should handle SIGINT gracefully.

**Textual Handling**:

From Textual source analysis:

```python
# Textual catches Ctrl+C and converts to exit
class App:
    def __init__(self):
        # Ctrl+C is trapped and requires Ctrl+Q to quit (v0.47.0+)
        # Or use allow CTRL_C flag
        pass
```

**Evidence** ([Textual Issue #5385](https://github.com/Textualize/textual/issues/5385)):
> "With the recent change to trapping Ctrl+C and asking the user to press Ctrl+Q..."

**Configuration**:
- `TEXTUAL_ALLOW_SIGINT=1`: Allow Ctrl+C to quit (older behavior)
- Textual v0.47+ traps Ctrl+C by default

**For AOM TUI Mode**:

```python
class AOMApp(App):
    def on_mount(self):
        # Install custom signal handler
        signal.signal(signal.SIGINT, self._on_sigint)
    
    def _on_sigint(self, signum, frame):
        """Handle Ctrl+C."""
        self._signal = signum
        self.exit()
```

**For Compact Mode**:

```python
import signal

def run_compact():
    try:
        # Run ansible
        pass
    except KeyboardInterrupt:
        # SIGINT raises KeyboardInterrupt
        print("\n[Interrupted by user]")
        cleanup()
        sys.exit(130)  # Standard exit code for SIGINT
    finally:
        cleanup()
```

---

### 3.2 SIGTERM (kill command)

**Should**: Save session and clean up.

**Textual Handling** ([Issue #5140](https://github.com/Textualize/textual/issues/5140)):

```python
class MinimalApp(App[None]):
    _signal = None
    
    def on_mount(self) -> None:
        signal.signal(signal.SIGTERM, self.catch_signal)
        signal.signal(signal.SIGHUP, self.catch_signal)
    
    def catch_signal(self, signum, frame) -> None:
        self._signal = signum
        self.exit()
```

**Evidence**:
> "On macOS... when the terminal is closed (sending a SIGHUP to child processes)... Textual does shutdown, but not gracefully and stdin/stdout are messed up. Default signal handlers would improve that."

**For AOM**:

```python
class AOMApp(App):
    def on_mount(self):
        # Register signal handlers
        for sig in [signal.SIGTERM, signal.SIGHUP]:
            signal.signal(sig, self._on_signal)
    
    def _on_signal(self, signum, frame):
        """Handle termination signals."""
        # 1. Save session state (if TUI mode)
        if self.session:
            self.session.save()
        
        # 2. Schedule cleanup
        self.call_later(self._cleanup_and_exit, signum)
    
    async def _cleanup_and_exit(self, signum):
        """Clean up and exit."""
        # Restore terminal
        # Save logs
        # Exit
        self.exit()
```

**Compact Mode**:

```python
import signal

def run_compact():
    def on_sigterm(signum, frame):
        # Set flag (signal-safe operation)
        terminate_flag.set()
    
    terminate_flag = threading.Event()
    signal.signal(signal.SIGTERM, on_sigterm)
    
    try:
        while not terminate_flag.is_set():
            # Run ansible
            pass
    finally:
        cleanup()
        sys.exit(143)  # 128 + 15 (SIGTERM)
```

---

### 3.3 SIGHUP (terminal closed)

**Should**: Save session and exit cleanly.

**Issue**: When terminal closes, all processes get SIGHUP.

**Textual**: Same as SIGTERM handling above.

**Compact Mode**: Same pattern - SIGHUP should clean up and exit.

**Important**: Write final summary before exiting:

```python
def on_sighup(signum, frame):
    # Write final summary to disk
    renderer.print_final_summary(file=sys.stderr)
    cleanup()
    sys.exit(129)  # 128 + 1 (SIGHUP)
```

---

### 3.4 SIGWINCH (terminal resize)

**Textual**: Handles automatically via `on_resize` event.

**Source**: [Textual Resize Event](https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md)

```python
class Placeholder(Static):
    def on_resize(self, event: events.Resize) -> None:
        """Update the placeholder with the new size."""
        # width, height available in event
        pass
```

**Textual automatically**:
1. Catches SIGWINCH
2. Queries new terminal size
3. Calls `on_resize()` on widgets
4. Re-renders the UI

**Compact Mode** (blessed):

**Source**: [blessed Measuring Docs](https://blessed.readthedocs.io/en/latest/measuring.html)

```python
# Modern: In-band resize (preferred)
term = Terminal()

if term.does_inband_resize(timeout=0.5):
    with term.notify_on_resize():
        while True:
            key = term.inkey(timeout=0.1)
            if key.name == 'RESIZE_EVENT':
                # Terminal resized
                new_height = term.height
                new_width = term.width
                render_status()
else:
    # Fallback: SIGWINCH (Unix only)
    if sys.platform != 'win32':
        resize_pending = threading.Event()
        
        def on_resize(*args):
            resize_pending.set()
        
        signal.signal(signal.SIGWINCH, on_resize)
```

**Warning from blessed docs**:
> "SIGWINCH has limitations: Not available on Windows. Signal handlers should avoid blocking operations."

**Best Practice**:

```python
class CompactRenderer:
    def __init__(self):
        self.term = Terminal()
        self.resize_event = threading.Event()
        
        # Try in-band first
        if self.term.does_inband_resize():
            self._use_inband_resize = True
        elif hasattr(signal, 'SIGWINCH'):
            signal.signal(signal.SIGWINCH, self._on_sigwinch)
            self._use_inband_resize = False
        else:
            # Windows without in-band: poll periodically
            self._use_polling = True
    
    def _on_sigwinch(self, signum, frame):
        """Signal handler - just set flag."""
        # SAFE: Only setting an Event (atomic operation)
        self.resize_event.set()
    
    def check_resize(self):
        """Call from main loop."""
        if self._use_inband_resize:
            # Handled by term.inkey()
            pass
        elif self.resize_event.is_set():
            self.resize_event.clear()
            self._handle_resize()
        elif self._use_polling:
            # Periodically check terminal size
            pass
    
    def _handle_resize(self):
        """Re-render status panel."""
        new_height = self.term.height
        new_width = self.term.width
        self.render_status()
```

---

### 3.5 SIGPIPE (broken pipe)

**Handling**: Python ignores SIGPIPE by default.

**Source**: [Python signal docs](https://docs.python.org/3/library/signal.html)

> "SIGPIPE is ignored (so write errors on pipes and sockets can be reported as ordinary Python exceptions)"

**For AOM**: No special handling needed. If user pipes output and pipe breaks:

```bash
# If user does this and kills grep:
aom site.yml | grep ERROR

# SIGPIPE will be raised as BrokenPipeError
# Python converts it to an exception
```

**Best Practice**: Catch the exception gracefully:

```python
try:
    for line in stream_output():
        print(line)
except BrokenPipeError:
    # Pipe closed (e.g., user killed grep)
    # Exit silently
    sys.exit(0)
```

**Important**: Restore default SIGPIPE handler for subprocess:

```python
import signal

# When spawning subprocess with pexpect
child = pexpect.spawn('ansible-playbook site.yml')

# pexpect handles signals correctly
# SIGPIPE goes to ansible-playbook process, not Python
```

---

## 4. TMUX/SCREEN SUPPORT

### 4.1 PTY Nesting Issues

**Architecture**:

```
Terminal Emulator (Ghostty, iTerm2, etc.)
    ↓ PTY 1
tmux server
    ↓ PTY 2 (virtual terminal)
shell (bash, zsh, etc.)
    ↓ PTY 3
python aom
    ↓ PTY 4 (if pexpect used)
ansible-playbook
```

**Evidence**: [Terminfo.dev - TTY Architecture](https://www.terminfo.dev/fundamentals/tty-architecture)

> "Terminal multiplexers like tmux and GNU Screen sit between your terminal emulator and your shell, creating virtual terminals inside your real terminal."

**Known Issues**:

#### Issue 1: Escape Sequence Pass-Through

**From** [Terminfo.dev - Multiplexers](https://terminfo.dev/multiplexers):

> "A multiplexer must understand an escape sequence to relay it correctly. When tmux encounters ESC[1m (bold), it knows what to do. But modern features? Not so much."

**Features often NOT passed through**:
- TrueColor (24-bit color)
- Sixel graphics
- Kitty keyboard protocol
- Some mouse modes

**Solution**: Use terminfo correctly:

```bash
# WRONG - uses outer terminal's terminfo inside tmux
export TERM=xterm-256color

# CORRECT - uses tmux's terminfo
export TERM=tmux-256color

# Or inside tmux, it's auto-set to:
TERM=screen-256color  # or tmux-256color
```

#### Issue 2: Mouse Support

**From** [tmux Issue #2721](https://github.com/tmux/tmux/issues/2721):

> "Mouse events (scrolling, in particular) are passed to the outermost tmux only..."

**Solution**:
- Use keyboard navigation instead of mouse in TUI mode
- Or configure tmux to pass mouse through: `set -g mouse on`

### 4.2 SIGWINCH in tmux

**Issue**: SIGWINCH timing in nested terminals.

**From** [tmux Issue #2341](https://github.com/tmux/tmux/issues/2341):

> "Tmux is, correctly, still reading from /dev/ttys004. The problem here is that your poetry shell command is creating a pty..."

**Key Insight**: When a nested PTY is created, SIGWINCH goes to the wrong process.

**For AOM**: If using pexpect inside tmux:
- pexpect creates PTY
- That PTY may not receive SIGWINCH from tmux
- Use blessed's in-band resize (DEC mode 2048) as fallback

### 4.3 Recommendations for AOM in tmux/screen

**Compact Mode**:
✅ **Works well** - No special issues
- Uses basic ANSI sequences (cursor positioning)
- Less reliant on modern terminal features

**TUI Mode**:
⚠️ **May have issues** - Test thoroughly
- TrueColor may degrade to 256 colors
- Mouse may not work properly
- Keyboard shortcuts may differ

**Testing Commands**:

```bash
# Check terminfo
infocmp | grep colors

# Test color support
echo -e '\033[38;2;255;0;0mTRUECOLOR RED\033[0m'

# Test mouse
# (run Textual demo)
textual demo

# Inside tmux, check:
tmux display -p '#{client_termfeatures}'
```

---

## 5. SSH SESSIONS

### 5.1 Does AOM Work Over SSH?

**Answer**: ✅ **Yes, both modes work.**

**Considerations**:

1. **Terminal detection**: SSH sets `TERM` environment variable
2. **Latency**: Network latency affects responsiveness
3. **Bandwidth**: Terminal updates consume bandwidth

### 5.2 Latency Issues

**Source**: [Ansible SSH Optimization](https://oneuptime.com/blog/post/2026-02-21-how-to-configure-ansible-for-slow-ssh-connections/view)

> "Not every server sits in a data center with a 1ms ping time... Sometimes you are managing hosts across continents, behind satellite links."

**Impact on AOM**:

**Compact Mode**:
- Rich Live updates at 4 FPS by default
- Each update sends ANSI sequences over SSH
- On high-latency links (500ms+ RTT), updates appear delayed

**TUI Mode**:
- More updates (mouse movements, key presses)
- Higher bandwidth usage
- More sensitive to latency

**Optimize Performance**:

```python
# Reduce refresh rate over SSH
if is_ssh_session():
    refresh_rate = 2  # Slower updates
else:
    refresh_rate = 4  # Default

live = Live(..., refresh_per_second=refresh_rate)
```

**Detect SSH**:

```python
import os

def is_ssh_session():
    """Check if running over SSH."""
    return (
        os.environ.get('SSH_CONNECTION') is not None or
        os.environ.get('SSH_CLIENT') is not None or
        os.environ.get('SSH_TTY') is not None
    )
```

### 5.3 Rich Live Over SSH Performance

**Source**: [SSH Performance Tips](https://devops.aibit.im/article/troubleshooting-ssh-latency-fixes)

> "SSH connection latency often stems from configuration oversights... Enable compression for high-latency links"

**Best Practices**:

1. **Enable SSH compression**:
   ```bash
   # ~/.ssh/config
   Host slow-remote
       Compression yes
       CompressionLevel 6
   ```

2. **Use SSH multiplexing**:
   ```bash
   Host *
       ControlMaster auto
       ControlPath ~/.ssh/sockets/%h-%p-%r
       ControlPersist 600
   ```

3. **Reduce ANSI output size**:
   ```python
   # Use fewer colors/styles over SSH
   if is_ssh_session():
       # Simplified rendering
       render_minimal_status()
   ```

### 5.4 Terminal Resize Over SSH

**Issue**: SIGWINCH may not always propagate over SSH.

**Solution**: Use blessed's in-band resize (DEC mode 2048) when available.

**From** blessed docs:
> "In-band resize notification support (DEC mode 2048) is currently very limited among terminal emulators... Provide a fallback using SIGWINCH on Unix"

---

## 6. TERMINAL RESIZE DETECTION

### 6.1 Textual (TUI Mode)

**Automatic**: Textual handles SIGWINCH internally.

**Source**: [Textual Resize Event](https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md)

```python
class MyWidget(Static):
    def on_resize(self, event: events.Resize) -> None:
        """Called automatically on terminal resize."""
        width = event.size.width
        height = event.size.height
        
        # Update layout
        self.update_layout(width, height)
```

**Added in Textual v0.46.0**: [In-band resize protocol](https://github.com/textualize/textual/blob/813aeeac/CHANGELOG.md)
> "Added support for in-band terminal resize protocol"

This means Textual can receive resize events via escape sequences, not just SIGWINCH.

### 6.2 Compact Mode (blessed)

**Three methods**:

#### Method 1: In-Band Resize (Preferred)

```python
from blessed import Terminal

term = Terminal()

if term.does_inband_resize(timeout=0.5):
    with term.notify_on_resize():
        while True:
            key = term.inkey(timeout=0.1)
            
            if key.name == 'RESIZE_EVENT':
                # Handle resize
                new_height = term.height
                new_width = term.width
                render_status()
```

**Note**: "In-band resize notification support (DEC mode 2048) is currently very limited among terminal emulators."

#### Method 2: SIGWINCH Fallback

```python
import signal
import threading

term = Terminal()
resize_event = threading.Event()

def on_sigwinch(signum, frame):
    """Signal handler - just set flag."""
    resize_event.set()

# Install handler (Unix only)
if hasattr(signal, 'SIGWINCH'):
    signal.signal(signal.SIGWINCH, on_sigwinch)

# In main loop
while running:
    if resize_event.is_set():
        resize_event.clear()
        new_height = term.height
        new_width = term.width
        render_status()
```

**Warning**:
> "SIGWINCH has limitations: Not available on Windows. Signal handlers should avoid blocking operations."

#### Method 3: Polling (Windows Fallback)

```python
import os
import time

last_size = None

while running:
    try:
        size = os.get_terminal_size()
        if size != last_size:
            last_size = size
            handle_resize(size.lines, size.columns)
    except OSError:
        # Not a TTY
        pass
    
    time.sleep(0.5)  # Poll every 500ms
```

---

## 7. OPEN QUESTIONS FOR IMPLEMENTATION

### OQ1: Should AOM warn users about terminal compatibility?

**Question**: When running in a terminal with limited capabilities (e.g., screen, old TERM), should AOM:
- Warn the user?
- Automatically adjust features?
- Refuse to run?

**Recommendation**:
- **Warn if `TERM` is unknown**: Check terminfo exists
- **Degrade gracefully**: If TrueColor unavailable, use 256 colors
- **Don't refuse**: Basic terminal support is sufficient for compact mode

**Implementation**:

```python
def check_terminal():
    """Check terminal compatibility."""
    import curses
    
    try:
        # Check terminfo
        curses.setupterm()
    except curses.error:
        print(f"Warning: Unknown terminal type: {os.environ.get('TERM')}")
        print("Some features may not work correctly.")
    
    # Check color depth
    console = Console()
    if console.color_system == 'standard':
        print("Note: Basic terminal detected. Using 16 colors.")
```

### OQ2: How to handle nested terminal detection?

**Question**: Should AOM detect if it's running inside tmux/screen and adjust behavior?

**Recommendation**: Detect and warn, but don't restrict.

**Implementation**:

```python
def detect_multiplexer():
    """Detect if running inside terminal multiplexer."""
    term = os.environ.get('TERM', '')
    
    if term.startswith('tmux'):
        return 'tmux'
    elif term.startswith('screen'):
        return 'screen'
    else:
        # Check for running in multiplexer without proper TERM
        # (user might have TERM=xterm-256color inside tmux)
        import sys
        if os.environ.get('TMUX'):
            return 'tmux'
        elif os.environ.get('STY'):
            return 'screen'
    
    return None

multiplexer = detect_multiplexer()
if multiplexer:
    print(f"Note: Running inside {multiplexer}. Some features may be limited.")
```

### OQ3: What is the minimum terminal size?

**Question**: What is the smallest terminal size AOM should support?

**Recommendation**:
- **Minimum**: 24 lines x 80 columns (standard VT100)
- **Compact mode**: Works at 24x80
- **TUI mode**: Recommend 30+ lines for full panels

**Implementation**:

```python
def check_terminal_size():
    """Check if terminal is large enough."""
    import os
    
    try:
        size = os.get_terminal_size()
        lines, columns = size.lines, size.columns
        
        min_lines = 24
        min_columns = 80
        
        if lines < min_lines:
            print(f"Warning: Terminal height ({lines}) is below minimum ({min_lines}).")
            print("Status display may be truncated.")
        
        if columns < min_columns:
            print(f"Warning: Terminal width ({columns}) is below minimum ({min_columns}).")
            print("Output may wrap incorrectly.")
        
        return lines, columns
    except OSError:
        # Not a TTY - use defaults
        return 24, 80
```

### OQ4: How to handle SSH session detection and optimization?

**Question**: Should AOM detect SSH sessions and automatically reduce refresh rate?

**Recommendation**: Yes, but also allow user override.

**Implementation**:

```python
def get_refresh_rate():
    """Get optimal refresh rate based on environment."""
    import os
    
    default_rate = 4
    ssh_rate = 2
    
    # Check if SSH session
    if any(os.environ.get(k) for k in ['SSH_CONNECTION', 'SSH_CLIENT', 'SSH_TTY']):
        return ssh_rate
    
    return default_rate

# Allow override
refresh_rate = args.refresh_rate or get_refresh_rate()
live = Live(..., refresh_per_second=refresh_rate)
```

### OQ5: Should compact mode fall back to simple output if ANSI not supported?

**Question**: If `TERM=dumb` or equivalent, should AOM:
- Use simple text output (no ANSI)?
- Show warning?
- Exit with error?

**Recommendation**: Fall back gracefully, show summary at end.

**Implementation**:

```python
class CompactRenderer:
    def __init__(self):
        self.is_tty = sys.stdout.isatty()
        self.term = os.environ.get('TERM', '')
        self.use_ansi = self.is_tty and self.term not in ('dumb', 'unknown')
    
    def update_display(self):
        """Update display (TTY-aware)."""
        if self.use_ansi:
            # Use ANSI positioning
            self._render_tty()
        # else: Don't do live updates
    
    def print_final_summary(self):
        """Print final summary (always shown)."""
        print("\n" + "=" * 70)
        print("PLAY RECAP")
        print("=" * 70)
        # ... print summary ...
```

### OQ6: How to test terminal compatibility?

**Question**: Should AOM include a terminal compatibility test command?

**Recommendation**: Yes, provide `aom --test-terminal` command.

**Implementation**:

```python
def test_terminal():
    """Test terminal capabilities."""
    from rich.console import Console
    from blessed import Terminal
    import os
    
    console = Console()
    term = Terminal()
    
    print("Terminal Compatibility Test")
    print("=" * 40)
    
    # Environment
    print(f"TERM: {os.environ.get('TERM', 'not set')}")
    print(f"TTY: {sys.stdout.isatty()}")
    
    # Colors
    print(f"Colors: {console.color_system}")
    print(f"True color: {console.color_system == 'truecolor'}")
    
    # Unicode
    test_chars = "┃━┏┗┣┫✔✘⏱↑↓"
    print(f"Unicode box chars: {test_chars}")
    
    # Size
    try:
        size = os.get_terminal_size()
        print(f"Size: {size.columns}x{size.lines}")
    except:
        print("Size: unknown")
    
    # blessed capabilities
    print(f"Mouse: {term.does_standalone_mouse()}")
    print(f"In-band resize: {term.does_inband_resize()}")
    
    # Test rendering
    console.print("[bold green]✔ Bold green works![/bold green]")
    console.print("[dim yellow]✔ Dim yellow works![/dim yellow]")
    console.print("[link=https://example.com]✔ Hyperlinks work![/link]")
```

---

## SUMMARY

### Minimum Requirements

| Feature | Compact Mode | TUI Mode |
|---------|--------------|----------|
| **Python** | 3.8+ | 3.9+ |
| **Colors** | 16+ | 256+ |
| **Unicode** | Optional | Recommended |
| **Mouse** | No | Yes (for full functionality) |
| **TERM** | Valid terminfo | Valid terminfo |

### Terminal Compatibility

| Terminal | Compact | TUI | Notes |
|----------|---------|-----|-------|
| xterm/xterm-256color | ✅ | ✅ | Standard |
| kitty/alacritty/iTerm2 | ✅ | ✅ | Recommended |
| GNOME Terminal | ✅ | ✅ | Standard Linux |
| Windows Terminal | ✅ | ✅ | Best for Windows |
| macOS Terminal.app | ✅ | ⚠️ | 256 colors only |
| tmux/screen | ⚠️ | ⚠️ | Limited features |
| SSH | ✅ | ✅ | May need tuning |

### Signal Handling Summary

| Signal | What | Compact Mode | TUI Mode |
|--------|------|--------------|----------|
| SIGINT | Ctrl+C | Cleanup + exit | Save + exit |
| SIGTERM | kill | Save + exit | Save + exit |
| SIGHUP | Terminal closed | Save + exit | Save + exit |
| SIGWINCH | Resize | Re-render status | Handled by Textual |
| SIGPIPE | Broken pipe | Ignore | Ignore |

### Recommended Architecture

```python
# Signal handling for both modes
def setup_signal_handlers(app_or_renderer):
    """Setup signal handlers for AOM."""
    
    signals = {
        signal.SIGTERM: handle_graceful_exit,
        signal.SIGHUP: handle_graceful_exit,
    }
    
    # SIGINT handled specially (Ctrl+C)
    # - TUI: Textual may trap it (use TEXTUAL_ALLOW_SIGINT)
    # - Compact: KeyboardInterrupt
    
    for sig, handler in signals.items():
        signal.signal(sig, handler)

def handle_graceful_exit(signum, frame):
    """Save state and exit cleanly."""
    # 1. Save session (if applicable)
    # 2. Write final summary
    # 3. Cleanup terminal
    # 4. Exit with proper code
    sys.exit(128 + signum)
```

---

*Research completed 2026-04-20*


---

## Python TUI Application Logging Strategy Research (2026-04-20)

### Executive Summary

**Question**: How should AOM handle its own internal logging and error reporting (separate from Ansible's output)?

**Finding**: Best practices for Python TUI applications involve a **dual-handler approach**: logs to file for post-mortem debugging, and optional live debug panel in TUI mode. Use Python's `logging` module with `QueueHandler` for non-blocking async logging, and `platformdirs` for XDG-compliant log paths.

**Key Pattern**: Textual applications use `self.log()` for development-time logging (visible in textual console), but production apps should write persistent logs to `~/.local/state/aom/logs/` using rotating file handlers.

---

### LQ1: Where should AOM's own logs go?

**Recommendation**: **Both** - debug panel for live view (TUI mode), log file for post-mortem analysis.

**Evidence from Textual Framework**:

**Textual's Built-in Logging** ([GitHub issue #4663](https://github.com/Textualize/textual/issues/4663)):

From Will McGugan (Textual author):
> "You can use Python's logging system in your app. You can write to the dev tools with https://textual.textualize.io/guide/devtools/#textual-log, or configure it in any way you wish"

**Two Logging Modes**:

1. **Development Logging** (`self.log()`):
   - Visible in Textual devtools console (separate terminal)
   - Logs objects, not just strings
   - Not for end users

2. **Production Logging** (Python `logging` module):
   - File handlers for persistent logs
   - Standard log levels (DEBUG, INFO, WARNING, ERROR)
   - Structured output (JSONL or formatted text)

**Evidence from Rich/Textual Integration** ([Issue #3188](https://github.com/Textualize/textual/issues/3188)):

```python
from rich.logging import RichHandler
from textual.widgets import RichLog

class LoggingConsole(RichLog):
    """RichLog as logging handler destination."""
    
rich_log_handler = RichHandler(
    console=LoggingConsole(),
    rich_tracebacks=True,
)
logger.addHandler(rich_log_handler)
```

This shows how to route Python's `logging` module to a Textual `RichLog` widget for live debug panel.

---

### LQ2: Log File Path - XDG Compliance

**Recommendation**: Use `platformdirs.user_log_dir("aom")` → `~/.local/state/aom/log/`

**Evidence from XDG Base Directory Specification**:

From [XDG spec](https://specifications.freedesktop.org/basedir/latest/):

> `$XDG_STATE_HOME` defines the base directory relative to which user-specific state files should be stored. If `$XDG_STATE_HOME` is either not set or empty, a default equal to `$HOME/.local/state` should be used. The `$XDG_STATE_HOME` contains state data that should persist between (application) restarts, but that is not important or portable enough to the user that it should be stored in `$XDG_DATA_HOME`. It may contain: actions history (logs, history, recently used files, …)

**Evidence from platformdirs**:

From [platformdirs documentation](https://platformdirs.readthedocs.io/en/latest/platforms.html):

| Platform | `user_log_dir("SuperApp")` |
|----------|----------------------------|
| Linux | `~/.local/state/SuperApp/log` |
| macOS | `~/Library/Logs/SuperApp` |
| Windows | `C:\Users\<User>\AppData\Local\Acme\SuperApp\Logs` |

**Usage**:

```python
from platformdirs import PlatformDirs

dirs = PlatformDirs("aom", "aom")
log_file = dirs.user_log_path / "aom.log"
# Linux: ~/.local/state/aom/log/aom.log
# macOS: ~/Library/Logs/aom/aom.log
# Windows: %LOCALAPPDATA%\aom\aom\Logs\aom.log
```

---

### LQ3: Log Levels - What Should AOM Log?

**Recommendation**: Use all standard log levels with clear separation of concerns.

| Level | Purpose | Examples |
|-------|---------|----------|
| **DEBUG** | Verbose internal state | JSONL events received, state machine transitions, pexpect raw output, parser decisions |
| **INFO** | High-level milestones | Playbook start/end, session creation, config loaded, host discovered |
| **WARNING** | Recoverable issues | `--list-tasks` failed (fallback applied), JSON parse error (skipping line), password prompt detected |
| **ERROR** | Failures requiring attention | Unexpected errors, subprocess crash, missing dependency |

**Evidence from Python Logging Best Practices**:

From [Python logging guide](https://docs.python.org/3.15/howto/logging-cookbook.html):

> "Loggers are plain Python objects. The addHandler() method has no minimum or maximum quota for the number of handlers you may add."

**Recommended Handler Configuration**:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure AOM's internal logging."""
    
    logger = logging.getLogger("aom")
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # File handler - DEBUG level (full detail for post-mortem)
    log_dir = platformdirs.user_log_dir("aom")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_dir / "aom.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # Debug panel handler - INFO level (for TUI)
    # Only added in TUI mode
    debug_panel_handler = QueueHandler(queue)
    debug_panel_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(debug_panel_handler)  # Only in TUI mode
    
    return logger
```

---

### LQ4: Log Rotation Policy

**Recommendation**: Use `RotatingFileHandler` with 10 MB per file, 5 backup files (50 MB max).

**Evidence from Python Logging Best Practices**:

From [Python logging handlers docs](https://docs.python.org/3.15/library/logging.handlers.html):

> `RotatingFileHandler`: Rotates based on file size. Once a log file reaches a certain limit, it's archived and a new file is created.

From [Production logging guide](https://uptimerobot.com/knowledge-hub/logging/python-logging-explained/):

> **Size-based rotation**: Best when traffic is unpredictable. Easy to cap disk use with `maxBytes * (backupCount + 1)`.

**Ansible's Log Path**:

From [Ansible config docs](https://docs.ansible.com/ansible/latest/reference_appendices/config.html):

> `DEFAULT_LOG_PATH`: File to which Ansible will log on the controller. When not set the logging is disabled.

Ansible does NOT rotate logs by default - logs go wherever configured. AOM should be better.

**Recommended Policy**:

```python
# Match AOM's session rotation policy (keep last N sessions)
# Logs: 10 MB per file, 5 backups = 50 MB max
handler = RotatingFileHandler(
    filename=log_dir / "aom.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8",
)
# Creates: aom.log, aom.log.1, aom.log.2, aom.log.3, aom.log.4, aom.log.5
```

---

### LQ5: Non-Blocking Logging for TUI

**Recommendation**: Use `QueueHandler` + `QueueListener` for async logging without blocking UI.

**Evidence from Python Logging Cookbook**:

From [Python docs](https://docs.python.org/3.15/howto/logging-cookbook.html):

> "You can use a QueueHandler to handle logging from multiple processes. The main process sets up a QueueHandler and a QueueListener..."

**Evidence from Async Logging Guide**:

From [kazis.dev](https://www.kazis.dev/blogs/python-async-logging):

> "Asynchronous logging solves this by offloading the logging work to a background thread. The good part is you don't need a third-party library to achieve this. Python's standard library provides the `logging.handlers.QueueHandler` and `logging.handlers.QueueListener` for this exact purpose."

**Implementation**:

```python
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

def setup_async_logging():
    """Setup non-blocking logging for TUI app."""
    
    # Queue for log messages
    log_queue = Queue(-1)  # Unlimited size
    
    # QueueHandler - threadsafe, non-blocking
    queue_handler = QueueHandler(log_queue)
    
    # Actual handlers (run in listener thread)
    file_handler = RotatingFileHandler(...)
    console_handler = logging.StreamHandler()
    
    # QueueListener - runs in separate thread
    listener = QueueListener(
        log_queue,
        file_handler,
        console_handler,
        respect_handlers_level=True,
    )
    listener.start()
    
    # Attach QueueHandler to logger
    logger = logging.getLogger("aom")
    logger.addHandler(queue_handler)
    
    return logger, listener
```

**Why This Matters for TUI**:

From [SuperFastPython](https://superfastpython.com/asyncio-log-blocking/):

> "You can log in asyncio programs without blocking using a QueueHandler and QueueListener. A queue.Queue can be created and used to store log messages... attach only a QueueHandler to those loggers which are accessed from performance-critical threads."

**For AOM**:
- Main TUI thread: Uses `QueueHandler` (instant, non-blocking)
- Listener thread: Writes to file (can block, doesn't affect UI)
- Debug panel: Can read from same queue

---

### LQ6: `--verbose` Flag Behavior

**Current Spec**: "Show resolved command, environment, terminal capabilities, and parsed task summary before execution"

**Additional Runtime Behavior**:

**Recommendation**: `--verbose` should:

1. **Before execution**: Print resolved command + environment + terminal capabilities + task summary (as specified)
2. **During runtime**: Set log level to DEBUG for file handler (more detail to logs)
3. **During runtime**: Enable debug panel in TUI mode (if not already shown)

**Evidence from Python CLI Logging Patterns**:

From [Production logging guide](https://thelinuxcode.com/how-to-log-python-messages-to-both-stdout-and-files-with-production-grade-patterns/):

> "Different levels per handler: I often log INFO to stdout but DEBUG to file. That keeps live logs readable but still captures deep details locally."

```python
import click

@click.command()
@click.option('--verbose', '-v', count=True)
def main(verbose):
    """AOM - Ansible Output Monitor."""
    
    # Configure logging based on verbosity
    logger = logging.getLogger("aom")
    
    if verbose >= 1:
        # DEBUG to file, INFO to console/panel
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.INFO)
    
    if verbose >= 2:
        # DEBUG to everything
        console_handler.setLevel(logging.DEBUG)
    
    # Print resolved command (verbose mode)
    if verbose:
        print(f"Resolved command: {resolved_cmd}")
        print(f"Environment: {env_vars}")
        print(f"Terminal: {terminal_caps}")
```

---

### LQ7: Error Handling - ansible-playbook Not Found

**Recommendation**: Clean error message with install instructions, exit code 127 (command not found).

**Evidence from CLI Best Practices**:

From [shutil.which examples](https://github.com/Panniantong/Agent-Reach/blob/main/agent_reach/cli.py):

```python
if shutil.which("gh"):
    print("  ✅ gh CLI already installed")
else:
    print("  Installing gh CLI...")
    # ... auto-install logic
```

**For AOM**:

```python
import shutil
import sys

def check_dependencies():
    """Check that ansible-playbook is available."""
    
    ansible_playbook = shutil.which("ansible-playbook")
    
    if not ansible_playbook:
        print(
            "ERROR: ansible-playbook not found in PATH.\n"
            "\n"
            "AOM requires Ansible to be installed. Install with:\n"
            "\n"
            "  # Ubuntu/Debian:\n"
            "  sudo apt install ansible\n"
            "\n"
            "  # Fedora:\n"
            "  sudo dnf install ansible\n"
            "\n"
            "  # macOS:\n"
            "  brew install ansible\n"
            "\n"
            "  # pip (all platforms):\n"
            "  pip install ansible\n",
            file=sys.stderr,
        )
        sys.exit(127)  # Standard exit code for command not found
    
    return ansible_playbook
```

---

### LQ8: Error Handling - ansible.posix or Other Dependencies Not Found

**Current Spec**: "Offer to install ansible.posix if not found"

**Generalized Recommendation**: Detect missing collections and offer to install them.

**Ansible Collection Dependencies**:

From [Ansible docs](https://docs.ansible.com/ansible/latest/reference_appendices/config.html):

```python
# Check if ansible.posix is available
import subprocess
import json

def check_ansible_collection(collection_name: str) -> bool:
    """Check if an Ansible collection is installed."""
    
    result = subprocess.run(
        ["ansible-galaxy", "collection", "list", "--format", "json"],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return False
    
    collections = json.loads(result.stdout)
    return any(
        collection_name in collection_id
        for collection_id in collections.keys()
    )

def install_collection(collection_name: str) -> bool:
    """Offer to install a missing collection."""
    
    print(f"WARNING: Collection '{collection_name}' not found.")
    
    # In TUI mode: show modal
    # In compact mode: prompt on stderr
    
    response = input(f"Install '{collection_name}' now? [Y/n] ")
    
    if response.lower() in ("", "y", "yes"):
        subprocess.run(
            ["ansible-galaxy", "collection", "install", collection_name],
            check=True,
        )
        return True
    
    return False
```

---

### LQ9: Python Logging Module Integration with Textual

**Question**: How to route Python's `logging` module to Textual's `RichLog` widget for debug panel?

**Evidence from Textual Community**:

From [GitHub issue #3188](https://github.com/Textualize/textual/issues/3188):

```python
import logging
from rich.logging import RichHandler
from textual.app import App, ComposeResult
from textual.widgets import RichLog

class LoggingConsole(RichLog):
    """RichLog widget acting as a console for RichHandler."""
    file = False
    console: Widget
    
    def print(self, content):
        self.write(content)

logger = logging.getLogger(__name__)
rich_log_handler = RichHandler(
    console=LoggingConsole(),  # type: ignore
    rich_tracebacks=True,
)
logger.addHandler(rich_log_handler)
logger.setLevel(logging.DEBUG)
```

**Alternative: Custom Handler for Textual**:

```python
from logging import Handler
from textual.widgets import RichLog
import queue

class TextualLogHandler(Handler):
    """Handler that sends log records to a Textual RichLog widget."""
    
    def __init__(self, rich_log: RichLog, queue: queue.Queue):
        super().__init__()
        self.rich_log = rich_log
        self.queue = queue
    
    def emit(self, record):
        """Queue log record for writing to RichLog."""
        try:
            msg = self.format(record)
            # Queue the message for the UI thread to process
            self.queue.put(msg)
        except Exception:
            self.handleError(record)
```

**Integration with QueueHandler**:

```python
from logging.handlers import QueueHandler

# Create queue for logs
log_queue = queue.Queue(-1)

# QueueHandler for non-blocking logging
queue_handler = QueueHandler(log_queue)

# Attach to logger
logger = logging.getLogger("aom")
logger.addHandler(queue_handler)

# In Textual app, poll queue and write to RichLog
class AOMApp(App):
    def compose(self):
        yield RichLog(id="debug-panel")
    
    async def on_mount(self):
        self.set_interval(0.1, self._poll_log_queue)
    
    async def _poll_log_queue(self):
        """Poll log queue and write to debug panel."""
        log = self.query_one("#debug-panel", RichLog)
        while not log_queue.empty():
            msg = log_queue.get_nowait()
            log.write(msg)
```

---

### LQ10: Should AOM Log Ansible's Output?

**Clarification**: This question is about AOM's **OWN** logs, not Ansible's output.

**Recommendation**: AOM should log:

1. **AOM's internal events** (to AOM's log file):
   - State transitions
   - Parser events
   - UI actions
   - Errors

2. **NOT Ansible's stdout/stderr**:
   - Ansible has its own logging (`log_path` in `ansible.cfg`)
   - AOM displays Ansible output in TUI
   - AOM stores Ansible output in session files (separate concern)

**Separation of Concerns**:

```
~/.local/state/aom/
├── log/
│   └── aom.log           # AOM's internal logs
├── sessions/
│   ├── session-20260420-143052.jsonl  # Ansible output (events)
│   └── session-20260420-143052.stdout # Ansible raw stdout
```

**What Goes in aom.log**:

```log
2026-04-20 14:30:52 [INFO] aom: Session started: session-20260420-143052
2026-04-20 14:30:52 [INFO] aom: Config loaded from ~/.config/aom/config.toml
2026-04-20 14:30:52 [DEBUG] aom.parser: Received JSONL: {"event": "playbook_on_start", ...}
2026-04-20 14:30:52 [DEBUG] aom.state: State transition: IDLE -> RUNNING
2026-04-20 14:30:53 [WARNING] aom.parser: Failed to parse line: "some malformed output"
2026-04-20 14:31:05 [ERROR] aom.subprocess: ansible-playbook exited with code 2
```

---

## Summary: AOM Logging Architecture

### Final Recommendations

| Aspect | Recommendation |
|--------|----------------|
| **Log Destination** | Dual: file (`~/.local/state/aom/log/aom.log`) + debug panel (TUI mode) |
| **Non-Blocking** | Use `QueueHandler` + `QueueListener` for async logging |
| **Log Rotation** | `RotatingFileHandler`: 10 MB/file, 5 backups (50 MB max) |
| **Log Levels** | DEBUG (file), INFO+ (panel/configurable) |
| **Verbose Flag** | Enable DEBUG everywhere, show pre-execution info |
| **Error: ansible-playbook not found** | Exit 127, print install instructions |
| **Error: collection not found** | Offer to install via `ansible-galaxy` |
| **Integration with Textual** | Custom `TextualLogHandler` or `RichHandler` + queue polling |

### Implementation Skeleton

```python
# aom/logging_config.py

import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import Queue
from pathlib import Path
import platformdirs

def setup_logging(verbose: bool = False) -> tuple[logging.Logger, QueueListener | None]:
    """
    Setup AOM's internal logging.
    
    Returns:
        (logger, listener) - logger to use, listener to stop at shutdown
    """
    
    # Log file location (XDG-compliant)
    log_dir = Path(platformdirs.user_log_dir("aom"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "aom.log"
    
    # Queue for async logging
    log_queue = Queue(-1)
    
    # File handler (always DEBUG level)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # QueueListener (runs in background thread)
    listener = QueueListener(log_queue, file_handler)
    listener.start()
    
    # Logger setup
    logger = logging.getLogger("aom")
    logger.setLevel(logging.DEBUG)
    
    # QueueHandler (non-blocking)
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    
    # Console handler (only in verbose mode)
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            "[%(levelname)s] %(message)s"
        ))
        # Add to queue for async console output
        listener.handlers = (file_handler, console_handler)
    
    return logger, listener


# aom/cli.py

import shutil
import sys
import click

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--tui', is_flag=True, help='Run in full TUI mode')
def main(verbose: bool, tui: bool):
    """AOM - Ansible Output Monitor."""
    
    # Check dependencies
    ansible_playbook = shutil.which("ansible-playbook")
    if not ansible_playbook:
        print(
            "ERROR: ansible-playbook not found in PATH.\n"
            "Install Ansible: pip install ansible",
            file=sys.stderr,
        )
        sys.exit(127)
    
    # Setup logging
    logger, listener = setup_logging(verbose=verbose)
    
    logger.info(f"AOM started (verbose={verbose}, tui={tui})")
    logger.debug(f"ansible-playbook found at: {ansible_playbook}")
    
    try:
        if tui:
            # Full TUI mode
            from aom.tui import AOMApp
            app = AOMApp()
            app.run()
        else:
            # Compact mode
            from aom.compact import run_compact_mode
            run_compact_mode()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise
    finally:
        # Cleanup
        logger.info("AOM shutting down")
        if listener:
            listener.stop()
```

---

*Research completed 2026-04-20*


---

## Ansible Strategy Callback Event Emission Patterns (2026-04-20)

### Executive Summary

**Key Finding**: The `v2_playbook_on_task_start` and `v2_runner_on_start` events serve fundamentally different purposes and are **NOT mutually exclusive**. All strategies emit `v2_playbook_on_task_start`, but `v2_runner_on_start` provides **additional per-host execution signaling**.

---

### EQ1: Linear Strategy Event Emission

**Context**: User asked which events the `linear` (default) strategy emits and when `v2_playbook_on_task_start` vs `v2_runner_on_start` are emitted.

**Evidence from Ansible Source Code**:

#### Linear Strategy (`lib/ansible/plugins/strategy/linear.py`)

**Event Emission Pattern**:

From [linear.py lines 184-195](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/linear.py#L184-L195):

```python
if not callback_sent:
    task.post_validate_attribute("name", templar=templar)

    if isinstance(task, Handler):
        self._tqm.send_callback('v2_playbook_on_handler_task_start', task)
    else:
        self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
    callback_sent = True

self._blocked_hosts[host_name] = True
self._queue_task(host, task, task_vars, play_context)
```

**Key Pattern**: The `linear` strategy emits `v2_playbook_on_task_start` **ONCE per task across ALL hosts** (controlled by `callback_sent` flag).

#### Base Strategy (`lib/ansible/plugins/strategy/__init__.py`)

**The `_queue_task` method emits `v2_runner_on_start`**:

From [\_\_init\_\_.py lines 407-413](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/__init__.py#L407-L413):

```python
worker_prc = WorkerProcess(
    shared_loader_obj=plugin_loader.get_plugin_loader_namespace(),
    worker_id=self._cur_worker,
    cliargs=context.CLIARGS,
)
self._workers[self._cur_worker] = worker_prc
self._tqm.send_callback('v2_runner_on_start', host, task)
worker_prc.start()
```

**Critical Discovery**: `v2_runner_on_start` is emitted in `_queue_task()` - **the BASE CLASS method** - which is called by ALL strategies when queuing a task for a specific host.

---

### EQ2: Free Strategy Event Emission

**Context**: User heard that `free` strategy emits `v2_runner_on_start` instead of `v2_playbook_on_task_start`.

**Evidence**: **THIS IS INCORRECT**. The `free` strategy emits BOTH events, but with different timing.

#### Free Strategy (`lib/ansible/plugins/strategy/free.py`)

From [free.py lines 183-190](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/free.py#L183-L190):

```python
if isinstance(task, Handler):
    self._tqm.send_callback('v2_playbook_on_handler_task_start', task)
else:
    self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
self._queue_task(host, task, task_vars, play_context)
# each task is counted as a worker being busy
workers_free -= 1
```

**Key Difference**:
- `linear`: Emits `v2_playbook_on_task_start` **once before processing all hosts**, then queues each host sequentially
- `free`: Emits `v2_playbook_on_task_start` **every time before queuing each host** (no `callback_sent` flag check)

**Both strategies emit `v2_runner_on_start`** (via `_queue_task()`) for EACH host.

---

### EQ3: Serial Strategy

**Context**: User asked how `serial` affects event emission.

**Finding**: `serial` is **NOT a separate strategy**. It's a play-level directive that affects batching.

From documentation search:

```yaml
- hosts: webservers
  strategy: linear  # or free
  serial: 5  # Process 5 hosts at a time
```

**Behavior**:
- `serial` limits the number of hosts processed concurrently
- Does not change which events are emitted
- Works with both `linear` and `free` strategies
- Under `linear` + `serial`: Processes batch → all tasks → next batch
- Under `free` + `serial`: Each batch processes independently, hosts within batch run as fast as possible

---

### EQ4: Other Strategies (host_pinned, etc.)

**Context**: User asked about other strategies and their event emission patterns.

**Evidence from Source Code**:

#### host_pinned Strategy (`lib/ansible/plugins/strategy/host_pinned.py`)

From [host_pinned.py lines 38-43](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/host_pinned.py#L38-L43):

```python
from ansible.plugins.strategy.free import StrategyModule as FreeStrategyModule

class StrategyModule(FreeStrategyModule):
    def __init__(self, tqm):
        super(StrategyModule, self).__init__(tqm)
        self._host_pinned = True
```

**Finding**: `host_pinned` is a **subclass of `free`** with only one difference: sets `self._host_pinned = True`.

From [free.py line 56](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/free.py#L56):
```python
self._host_pinned = False
```

The `_host_pinned` flag affects worker allocation (see [free.py lines 195-198](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/free.py#L195-L198)) but **does NOT change event emission**.

#### Available Strategies (from Ansible 2.7+):

From [strategy plugins documentation](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/strategy_plugin.html):
- `linear` - Default, lockstep execution
- `free` - As fast as possible per host
- `host_pinned` - Host-pinned execution (extends free)
- `debug` - Interactive debugging

**All strategies inherit from `StrategyBase`** and call `_queue_task()`, which emits `v2_runner_on_start`.

---

### EQ5: Default Callback Behavior for Free/Host_Pinned

**Context**: User asked what the default callback does when `v2_playbook_on_task_start` arrives but strategy is "free".

**Evidence from Default Callback**:

From [default.py lines 148-169](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/callback/default.py#L148-L169):

```python
def v2_playbook_on_task_start(self, task, is_conditional):
    self._task_start(task, prefix='TASK')

def _task_start(self, task, prefix=None):
    # Cache output prefix for task if provided
    # This is needed to properly display 'RUNNING HANDLER' and similar
    if prefix is not None:
        self._task_type_cache[task._uuid] = prefix

    # Preserve task name, as all vars may not be available for templating
    # when we need it later
    if self._play.strategy in add_internal_fqcns(('free', 'host_pinned')):
        # Explicitly set to None for strategy free/host_pinned to account for any cached
        # task title from a previous non-free play
        self._last_task_name = None
    else:
        self._last_task_name = task.get_name().strip()

        # Display the task banner immediately if we're not doing any filtering based on task result
        if self.get_option('display_skipped_hosts') and self.get_option('display_ok_hosts'):
            self._print_task_banner(task)
```

**Critical Insight from code comments** (lines 160-163):

```python
# Explicitly set to None for strategy free/host_pinned to account for any cached
# task title from a previous non-free play
self._last_task_name = None
```

**What This Means**:
1. The default callback **DOES NOT IGNORE** `v2_playbook_on_task_start` for free/host_pinned
2. Instead, it **delays printing the task banner** until it receives a result (ok/changed/failed)
3. The `self._last_task_name = None` prevents stale task names from previous plays
4. Task banners are printed on-demand per-host based on results (see [default.py lines 80-86](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/callback/default.py#L80-L86))

From [default.py lines 207-209](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/callback/default.py#L207-L209):

```python
def v2_runner_on_start(self, host, task):
    if self.get_option('show_per_host_start'):
        self._display.display(" [started %s on %s]" % (task, host), color=C.COLOR_OK)
```

**The `v2_runner_on_start` event is used for OPT-IN per-host start notification** (disabled by default, enabled via `show_per_host_start` callback option).

---

### Summary Table: Event Emission by Strategy

| Event | linear | free | host_pinned | debug |
|-------|--------|------|-------------|-------|
| `v2_playbook_on_task_start` | **Once per task** (all hosts) | **Per host** (when queuing) | Same as free | Same as linear |
| `v2_runner_on_start` | **Per host** (via `_queue_task`) | **Per host** (via `_queue_task`) | Same as free | Same as linear |
| `v2_playbook_on_handler_task_start` | Once per handler | Per host for handlers | Same as free | Same as linear |

---

### Event Timing Diagram

#### Linear Strategy:

```
Time →
Task 1 begins:
  → v2_playbook_on_task_start(task)  [ONCE]
  → for host1:
      → v2_runner_on_start(host1, task)  [via _queue_task]
      → v2_runner_on_ok/failed/... (result)
  → for host2:
      → v2_runner_on_start(host2, task)
      → v2_runner_on_ok/failed/... (result)
Task 2 begins:
  → v2_playbook_on_task_start(task)  [ONCE]
  → ... (repeat pattern)
```

#### Free Strategy:

```
Time →
Task 1 begins:
  → for host1:
      → v2_playbook_on_task_start(task)  [PER HOST]
      → v2_runner_on_start(host1, task)
      → v2_runner_on_ok/failed/... (result)
  → for host2 (may interleave):
      → v2_playbook_on_task_start(task)  [PER HOST]
      → v2_runner_on_start(host2, task)
      → v2_runner_on_ok/failed/... (result)
Task 2 (may start for host1 while host2 still on task1):
  → for host1:
      → v2_playbook_on_task_start(task)  [PER HOST]
      → v2_runner_on_start(host1, task)
      ...
```

---

### Implications for AOM State Machine

**Critical Insights for Implementation**:

1. **Both Events Are Emitted**: Monitor for BOTH `v2_playbook_on_task_start` AND `v2_runner_on_start`

2. **State Model**:
   ```python
   class TaskState:
       task_uuid: str
       name: str
       
       # For linear: set from v2_playbook_on_task_start
       # For free: updated on each v2_playbook_on_task_start
       announced_at: datetime
       
       # Per-host tracking from v2_runner_on_start
       hosts_started: set[str] = {}      # from v2_runner_on_start
       hosts_completed: set[str] = {}     # from v2_runner_on_ok/failed/...
   ```

3. **Task Banner Logic** (mimic default callback):
   ```python
   def on_task_start(self, event):
       if event.strategy in ('free', 'host_pinned'):
           # Don't print banner - wait for per-host results
           self._pending_task_name = event.task.name
       else:
           # Print banner immediately
           self.print_task_banner(event.task)
   ```

4. **Use `v2_runner_on_start` For**:
   - Real-time per-host task execution tracking
   - Calculating "currently running" hosts
   - Showing parallelism (host X started before Y finished)

5. **Default Callback Option**: `show_per_host_start` must be enabled in ansible.cfg:
   ```ini
   [defaults]
   callback_plugins = /path/to/aom/callback
   callback_whitelist =profile_tasks
   stdout_callback = default
   
   [callback_default]
   show_per_host_start = yes
   ```

---

### References

- **Ansible Repository**: https://github.com/ansible/ansible
- **Commit**: bd7fa60c2413a26a5657c739db6ec107ca7ecb0b
- **Key Files**:
  - [lib/ansible/plugins/strategy/linear.py](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/linear.py)
  - [lib/ansible/plugins/strategy/free.py](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/free.py)
  - [lib/ansible/plugins/strategy/host_pinned.py](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/host_pinned.py)
  - [lib/ansible/plugins/strategy/__init__.py](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/strategy/__init__.py) (line 410: `v2_runner_on_start`)
  - [lib/ansible/plugins/callback/default.py](https://github.com/ansible/ansible/blob/bd7fa60c2413a26a5657c739db6ec107ca7ecb0b/lib/ansible/plugins/callback/default.py)

---

*Research completed 2026-04-20*
