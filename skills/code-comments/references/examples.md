# Comment examples

Before/after pairs from the owner's feedback. Each entry is generalized: renamed identifiers, no private code. These outrank the general advice in `SKILL.md`. Keep about 20 entries: merge duplicates, and when two lessons conflict, the newer one wins.

## 1. Comment the line that does it, not the loop header

**Before**
```python
for a, b, close in edges:  # related nodes sit near each other
    dist = max(math.hypot(dx, dy), 0.01)
    pull = dist**2 / (SPACING * (0.6 if close else 1))
```
**After**
```python
for a, b, close in edges:  # each edge pulls its two ends together
    dist = max(math.hypot(dx, dy), 0.01)
    pull = dist**2 / (SPACING * (0.6 if close else 1))  # close edges pull harder
```
**Lesson:** the old comment described what one line does, but sat on the loop. Put each claim on the line that makes it true.

## 2. Explain every magic multiplier

**Before**
```python
push = SPACING**2 / dist * (4 if a in pinned or b in pinned else 1)
```
**After**
```python
push = SPACING**2 / dist * (4 if a in pinned or b in pinned else 1)  # pinned nodes push 4x: keeps the center clear
```
**Lesson:** a bare `4` makes readers guess. Say what it achieves.

## 3. Name what a guard protects against

**Before**
```python
dist = max(math.hypot(dx, dy), 0.01)
```
**After**
```python
dist = max(math.hypot(dx, dy), 0.01)  # floor: no divide-by-zero if two nodes overlap
```
**Lesson:** guards look like noise until you say what they prevent.

## 4. Say the idea behind a step, not its arithmetic

**Before**
```python
step *= 0.985
```
**After**
```python
step *= 0.985  # cool down: smaller moves each round so the layout settles
```
**Lesson:** "multiply by 0.985" is already in the code. The comment should name the technique.

## 5. Surface hidden assumptions in estimates

**Before**
```python
width = len(label) * 6 + 4
```
**After**
```python
width = len(label) * 6 + 4  # rough label width: ~6px per character + padding
```
**Lesson:** an estimate hides an assumption (font size, units). Write it down so it can be checked.

## 6. Dense logic gets one comment per decision

**Before**
```python
axis, over = (0, over_x) if over_x < over_y else (1, over_y)
sign = 1 if pos[a][axis] >= pos[b][axis] else -1
share = 0 if a in pinned else 1 if b in pinned else 0.5
```
**After**
```python
axis, over = (0, over_x) if over_x < over_y else (1, over_y)  # separate along the smaller overlap
sign = 1 if pos[a][axis] >= pos[b][axis] else -1  # push a away from b
share = 0 if a in pinned else 1 if b in pinned else 0.5  # pinned nodes stay put; the other moves
```
**Lesson:** three dense lines are three decisions. Give each one a few words.
