QCAD is required to run the CAD-detail skill. Please ensure QCAD is installed and accessible. If you need to install QCAD, you can use Homebrew Cask:

brew install --cask qcad

If prompted for a password, you will need to provide your system password (or use the -S option to supply it via stdin). Once QCAD is installed at /Applications/QCAD.app, the skill can be invoked with:

/Applications/QCAD.app/Contents/MacOS/QCAD -no-gui -allow-multiple-instances -autostart /tmp/<script_name>.js

If QCAD is installed elsewhere, adjust the path accordingly.