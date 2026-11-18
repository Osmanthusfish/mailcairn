MailCairn desktop runtime notices
===============================

This directory accompanies the Windows desktop build. Third-party components
retain their own licenses; MailCairn's noncommercial source license does not
replace those licenses or restrict rights granted by them.

The Python interpreter and third-party native libraries are bundled unmodified.
MailCairn application modules, static resources and a PyInstaller launcher are
combined with the runtime. No modifications to upstream Python/Tcl/Tk/OpenSSL
source are claimed.

Python-Windows-LICENSE.txt includes the applicable Python, historical, and
Windows binary redistribution conditions, including Microsoft Distributable
Code conditions. Preserve this entire file. Python-incorporated-software-
notices.txt contains additional Python component licenses, including the full
mimalloc MIT terms. Tcl/Tk, OpenSSL, Expat, zlib and other components have their
own separate notices in this directory.

PyInstaller-COPYING.txt includes its bootloader exception and Apache-2.0 runtime
hook terms. The separate Apache text and runtime-hook notice list are included
for clarity. Listing all installed runtime-hook copyright headers is a
conservative notice collection and does not assert every hook was embedded.

The source URLs, access dates, selected component versions, transformations,
and SHA-256 values are recorded in manifest.json. The *.txt notice files are
either copied exactly or retain the complete leading source copyright/license
comment as indicated there. Source implementation code has not been copied.

See docs/desktop-dependencies.md in the source release for audit boundaries.
No legal-clearance, authenticity, security-certification or public-release claim
is made merely by including these notices.
