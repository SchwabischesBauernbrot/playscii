# -*- mode: python -*-

import winreg

block_cipher = None

include_files = [
    ('./README.md', '.'),
    ('license.txt', '.'),
    ('*.cfg.default', '.'),
    ('version', '.'),
    ('art', 'art'),
    ('charsets', 'charsets'),
    ('palettes', 'palettes'),
    ('scripts', 'scripts'),
    ('shaders', 'shaders'),
    ('games', 'games'),
    ('ui/*.png', 'ui'),
    ('docs/html/*.*', 'docs/html')
]

include_bins = [
    ('./*.dll', '.'),
    (winreg.ExpandEnvironmentStrings('%WINDIR%') + '\\system32\\version.dll', '.')
]

a = Analysis(['playscii.py'],
             pathex=['.'],
             binaries=include_bins,
             datas=include_files,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='playscii',
          debug=False,
          strip=None,
          upx=True,
          icon='ui\playscii.ico',
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='playscii')
