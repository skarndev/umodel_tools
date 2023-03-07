import os
import traceback
import typing as t

import lark

with open(os.path.join(os.path.dirname(__file__), 'props_txt_grammar.lark')) as f:
    lark_parser = lark.Lark(f, parser='earley', propagate_positions=True, ambiguity='resolve')


t.overload
def parse_props_txt(props_txt_path: str, mode: t.Literal['MESH']) -> list[str]:
    ...

t.overload
def parse_props_txt(props_txt_path: str, mode: t.Literal['MATERIAL']) -> dict[str, str]:
    ...

def parse_props_txt(props_txt_path: str,
                     mode: t.Literal['MESH'] | t.Literal['MATERIAL']
                    ) -> list[str] | list[tuple[str, str]]:
    """Parses props.txt file (UModel output) and returns either a list of material paths, or a list of texture paths
    depending on the mode. Note, the mode should be used appropriately depending on the origin of the file.

    :param props_txt_path: Path to the prop.txt file.
    :param mode: Mode of parsing, either mesh properties or texture properties.
    :raises NotImplementedError: Raised when not supported mode is passed.
    :raises OSError: Raised when reading the file failed.
    :return: A list of relative paths (game format paths).
    """
    with open(props_txt_path, 'r') as f:
        text = f.read()

        try:
            ast = lark_parser.parse(text)
        except lark.UnexpectedInput as e:
            print(f"ERROR: Failed parsing {props_txt_path}.")
            traceback.print_exc()
            raise OSError()

        match mode:
            case 'MESH':
                material_paths = []

                for child in ast.children:
                    assert child.data == 'definition'
                    def_name, array_qual, value = child.children

                    if def_name != 'Materials':
                        continue

                    assert array_qual is not None
                    assert value.data == 'structured_block'

                    for path_entry in value.children:
                        assert path_entry.data == 'definition'
                        _, _, path_desc = path_entry.children

                        assert path_desc.data == 'path'

                        _, path_value = path_desc.children
                        material_paths.append(path_value.children[0].value[1:][:-1])

                return material_paths

            case 'MATERIAL':
                texture_infos = {}

                for child in ast.children:
                    assert child.data == 'definition'
                    def_name, array_qual, value = child.children

                    if def_name != 'TextureParameterValues':
                        continue

                    assert array_qual is not None
                    assert value.data == 'structured_block'

                    for tex_param_def in value.children:
                        _, _, tex_param = tex_param_def.children
                        param_info, param_val, _ = tex_param.children
                        _, _, path_desc = param_val.children
                        assert path_desc.data == 'path'

                        _, path_value = path_desc.children

                        tex_path = path_value.children[0].value[1:][:-1]
                        tex_type = param_info.children[2].children[0].children[2].children[0].value

                        texture_infos[tex_type] = tex_path

                return texture_infos

            case _:
                raise NotImplementedError()
