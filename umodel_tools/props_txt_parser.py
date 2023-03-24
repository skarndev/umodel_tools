import os
import traceback
import typing as t

import lark


with open(os.path.join(os.path.dirname(__file__), 'props_txt_grammar.lark'), mode='r', encoding='utf-8') as grammar_f:
    lark_parser = lark.Lark(grammar_f, parser='earley', propagate_positions=True, ambiguity='resolve')


@t.overload
def parse_props_txt(props_txt_path: str, mode: t.Literal['MESH']) -> tuple[lark.Tree, list[str]]:
    ...


@t.overload
def parse_props_txt(props_txt_path: str,
                    mode: t.Literal['MATERIAL']
                    ) -> tuple[lark.Tree, dict[str, str], dict[str, str | float | bool]]:
    ...


def parse_props_txt(props_txt_path: str,
                    mode: t.Literal['MESH'] | t.Literal['MATERIAL']
                    ) -> tuple[lark.Tree, list[str]] | tuple[lark.Tree, dict[str, str], dict[str, str | float | bool]]:
    """Parses props.txt file (UModel output) and returns either a list of material paths, or a list of texture paths
    depending on the mode. Note, the mode should be used appropriately depending on the origin of the file.

    :param props_txt_path: Path to the prop.txt file.
    :param mode: Mode of parsing, either mesh properties or texture properties.
    :raises NotImplementedError: Raised when not supported mode is passed.
    :raises OSError: Raised when file could not be opened.
    :raises RuntimeError: Raised when reading the file failed.
    :return: A list of relative paths (game format paths).
    """
    print(f"Parsing {props_txt_path}...")
    with open(props_txt_path, mode='r', encoding='utf-8') as f:
        text = f.read()

        try:
            ast = lark_parser.parse(text)
        except lark.UnexpectedInput as e:
            print(f"ERROR: Failed parsing {props_txt_path}.")
            traceback.print_exc()
            raise RuntimeError

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

                return ast, material_paths

            case 'MATERIAL':
                texture_infos = {}
                base_prop_overrides = None

                for child in ast.children:
                    assert child.data == 'definition'
                    def_name, array_qual, value = child.children

                    match def_name:
                        case 'TextureParameterValues':
                            assert array_qual is not None
                            assert value.data == 'structured_block'

                            for tex_param_def in value.children:
                                _, _, tex_param = tex_param_def.children
                                param_info, param_val, _ = tex_param.children
                                _, _, path_desc = param_val.children

                                # ignore unused materials
                                if path_desc.data != 'path':
                                    continue

                                _, path_value = path_desc.children

                                tex_path = path_value.children[0].value[1:][:-1]
                                tex_type = param_info.children[2].children[0].children[2].children[0].value.strip()

                                texture_infos[tex_type] = tex_path
                        case 'BasePropertyOverrides':
                            assert array_qual is None
                            assert value.data == 'structured_block'

                            base_prop_overrides = {}

                            for prop_override_entry in value.children:
                                prop_name, _, prop_value = prop_override_entry.children
                                prop_name = prop_name.value

                                match prop_name:
                                    case 'BlendMode':
                                        prop_value = prop_value.children[0].value.strip()
                                    case 'TwoSided':
                                        prop_value = prop_value.children[0].value == 'true'
                                    case 'OpacityMaskClipValue':
                                        prop_value = float(prop_value.children[0].value)
                                    case _:
                                        continue

                                base_prop_overrides[prop_name] = prop_value

                return ast, texture_infos, base_prop_overrides

            case _:
                raise NotImplementedError()
