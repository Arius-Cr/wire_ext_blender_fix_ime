import sys
import os
import subprocess
import traceback
from pathlib import Path
import shutil
import argparse
import re

_dir = os.path.dirname(__file__)
_dir_dir = os.path.dirname(_dir)
sys.path.append(_dir_dir)
__package__ = os.path.basename(_dir)
del _dir
del _dir_dir

addon_name = 'wire_fix_ime'
addon_full_name = 'wire_ext_blender_fix_ime'

prj_dir = Path(__file__).parent

def make():
    parser_parent = argparse.ArgumentParser(add_help=False)

    parser = argparse.ArgumentParser(
        prog="make", description="生成工具")
    parser.add_argument('-v', '--vsdev', type=str, required=True,
        help="VsDevCmd.bat 文件的路径，"
        "如：C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/Tools/VsDevCmd.bat")
    parser.add_argument('-b', '--blender-dir', type=str, required=True,
        help="Blender 目录，用于 link、run 命令")

    subparsers = parser.add_subparsers(help="", dest="verbo")

    subparser = subparsers.add_parser('build', help="生成",
        parents=[parser_parent])
    subparser.add_argument('-c', '--config', choices=['debug', 'release'], default='debug', required=False,
        help="配置")
    subparser = subparsers.add_parser('link', parents=[parser_parent],
        help="链接到 Blender 的 addons 目录")
    subparser.add_argument('-c', '--config', choices=['debug', 'release'], default='debug', required=False,
        help="配置")

    subparser = subparsers.add_parser('run', parents=[parser_parent],
        help="运行 Blender")

    subparser = subparsers.add_parser('clean', parents=[parser_parent],
        help="清理")

    subparser = subparsers.add_parser('pack', parents=[parser_parent],
        help="打包")

    args, unknow_args = parser.parse_known_args()

    try:

        if args.verbo == 'build':
            build(args)

        elif args.verbo == 'link':
            link(args)

        elif args.verbo == 'run':
            run(args)

        elif args.verbo == 'clean':
            clean(args)

        elif args.verbo == 'pack':
            pack(args)

        else:
            print("请指定一个操作")
            print("----------")
            parser.print_help()

        print("\n执行结束")
        print("----------")

    except:
        traceback.print_exc()

    pass

def build(args):

    path_vsdevcmd = Path(args.vsdev)

    if args.config == 'debug':
        int_dir = prj_dir.joinpath('xbuild', 'debug')
        out_dir = prj_dir.joinpath('xdebug')
    elif args.config == 'release':
        int_dir = prj_dir.joinpath('xbuild', 'release')
        out_dir = prj_dir.joinpath('xrelease')

    os.makedirs(int_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    # 生成 DLL

    if not path_vsdevcmd.exists():
        print("找不到：%s" % path_vsdevcmd)
        print("请在 make.py 中将 path_vsdevcmd 设为当前系统所用版本")

    else:
        path_vsxproj = prj_dir.joinpath("native", "main.vcxproj")
        path_src_dir = prj_dir.joinpath("native")
        path_int_dir = int_dir.joinpath("int")
        path_out_dir = int_dir.joinpath("out")

        need_to_rebuild = True
        if path_out_dir.exists():

            mtime_src = 0
            for _name in os.listdir(path_src_dir):
                mtime_src = max(mtime_src, os.path.getmtime(path_src_dir.joinpath(_name)))

            mtime_out = 0
            for _name in os.listdir(path_out_dir):
                mtime_out = max(mtime_out, os.path.getmtime(path_out_dir.joinpath(_name)))

            if mtime_out > mtime_src:
                need_to_rebuild = False

        if need_to_rebuild:

            props: list[str] = []
            props.append('Configuration={}'.format(args.config.capitalize()))
            props.append('Platform=x64')
            props.append('IntDir={}\\'.format(path_int_dir))  # 必须以斜杠结尾
            props.append('OutDir={}\\'.format(path_out_dir))

            cmd = [
                'call', path_vsdevcmd, '&&',
                'msbuild.exe', path_vsxproj, '-property:' + ";".join(props)
            ]
            print("生成命令: %s\n" % cmd)

            p = subprocess.Popen(cmd, shell=True)
            (output, err) = p.communicate()
            p_status = p.wait()

            print("\n")

        else:
            print("无需重新编译")
            print("\n")

    # 复制文件

    if args.config == 'debug':
        _mark = (['mark.py'], [])
        _dll = (['xbuild', 'debug', 'out', 'native.dll'], ['native', 'native.dll'])
    elif args.config == 'release':
        _mark = (['mark.release.py'], ['mark.py'])
        _dll = (['xbuild', 'release', 'out', 'native.dll'], ['native', 'native.dll'])

    files = [
        (['__init__.py'], []),
        (['main.py'], []),
        _mark,
        (['native', '__init__.py'], []),
        _dll,
    ]

    for _src, _dst in files:
        if not _dst:
            _dst = _src

        _src_path = prj_dir.joinpath(*_src)
        _dst_path = out_dir.joinpath(*_dst)
        os.makedirs(_dst_path.parent, exist_ok=True)

        print("复制文件：%s" % str(_src))

        shutil.copyfile(_src_path, _dst_path)

    print("\n")
    print("生成完成")

    return 0

def link(args):

    blender_dir = Path(args.blender_dir)

    exe_path = blender_dir.joinpath("Blender.exe")

    if not exe_path.exists():
        print("找不到：", exe_path)
        return

    version: tuple[int, int, int] = None

    _rs = os.popen(f'"{exe_path}" -v')
    if _match := re.match(r'Blender (\d+).(\d+).(\d+)', _rs.readline()):
        version = (_match[1], _match[2], _match[3])
    else:
        print(_err := "无法获取版本信息")
        raise Exception(_err)

    dst = blender_dir.joinpath('%s.%s' % version[0:2], 'scripts', 'addons', addon_name)

    if os.path.lexists(dst):
        print("删除旧链接")
        os.unlink(dst)

    src = prj_dir.joinpath('xdebug' if args.config == 'debug' else 'xrelease')

    p = subprocess.Popen([
        'mklink', '/d', '/h', '/j', dst, src,
    ], shell=True)
    p.communicate()
    p.wait()

    pass

def run(args):

    blender_dir = Path(args.blender_dir)

    exe_path = blender_dir.joinpath("Blender.exe")

    if not exe_path.exists():
        print("找不到：", exe_path)
        return

    cmd = [exe_path]
    p = subprocess.Popen(cmd, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()

def clean(args):
    if (_dir := prj_dir.joinpath('xbuild')).exists():
        print("删除：%s" % _dir)
        shutil.rmtree(_dir)

    if (_dir := prj_dir.joinpath('xdebug')).exists():
        print("删除：%s" % _dir)
        shutil.rmtree(_dir)

    if (_dir := prj_dir.joinpath('xrelease')).exists():
        print("删除：%s" % _dir)
        shutil.rmtree(_dir)

    pass

def pack(args):
    dir = prj_dir.joinpath('xrelease')

    if not dir.exists():
        print("目录不存在：", dir)
        return

    try:

        import zipfile
        from . import bl_info  # 不要在 __init__.py 中引用 bpy

        version = '%s.%s.%s' % bl_info['version']
        file_name = f'{addon_full_name}_v{version}.zip'

        if (file_path := prj_dir.joinpath(file_name)).exists():
            os.remove(file_path)

        with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(dir, arcname=addon_name)
            for root, dirs, files in os.walk(dir):
                for fn in files:
                    zipf.write(
                        fp := os.path.join(root, fn),
                        arcname=addon_name + '/' + os.path.relpath(fp, dir)
                    )

        print("打包完成：%s" % file_path)

    except:
        traceback.print_exc()
        print("打包失败")


make()
