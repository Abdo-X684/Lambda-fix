# In-game test status

No GoldSrc engine runs in the build environment, so nothing below was tested automatically.
Status comes from reports by the user, marked as such.

| Item | Status | Source |
| --- | --- | --- |
| Game starts | Works | User report |
| BHL menu opens | Works | User report |
| Opposing Force weapons work | Works | User report |
| Ammo HUD crash | Fixed | User report after the `-O2` rebuild |
| Lag | Greatly reduced | User report on a weak PC |
| Auto-update removed from Advanced > About | Not tested | Source change only |
| Default HUD color green | Not tested | Source change only |
| Localization text (`bhlop4_english.txt`) | Not tested | File added, display not confirmed |
| Music on Linux | Not tested | — |
| Every campaign map (`of0a0` onward) | Not tested | — |
| Each weapon: fire, reload, switch, sound, model, effects | Not tested per weapon | — |
| Grapple, Penguin, Displacer, Shock Rifle special cases | Not tested | — |

## Suggested test list

1. Start a new game and confirm the first map loads from Opposing Force.
2. Open Advanced > About and confirm there is no update option.
3. Confirm the HUD is green.
4. Check each weapon: fire, reload, switch, sound, model.
5. Record any error from the console.
