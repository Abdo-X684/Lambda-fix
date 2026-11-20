BHL base + 10 OP4 weapon registrations (Linux, ELF32)
NOT TESTED IN GAME. Build verified only (compile + link + symbols).

Test with your WORKING original BugfixedHL setup (valve_addon -> gearbox_addon trick):
1. Back up your current  cl_dlls/client.so  and  dlls/hl.so  first.
2. Copy this folder's cl_dlls/client.so and dlls/hl.so over them.
3. Launch exactly as you do now (-game <your folder> -console).
4. Test the 10 OP4-only weapons: displacer, eagle, grapple, knife, m249,
   penguin, pipewrench, shockrifle, sniperrifle, sporelauncher.
   Give them with impulse 101 (or the give command), then fire / reload.
5. To revert: copy your backups back.
Report: which weapons animate correctly, and the console text (condebug log).
