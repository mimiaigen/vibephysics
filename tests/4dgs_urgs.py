import bpy
import mathutils
import os
import typing


def menu_switching_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize Menu Switching node group"""
    menu_switching_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="Menu Switching")

    menu_switching_1.color_tag = 'NONE'
    menu_switching_1.description = ""
    menu_switching_1.default_group_node_width = 140
    menu_switching_1.show_modifier_manage_panel = True

    # menu_switching_1 interface

    # Socket Output
    output_socket = menu_switching_1.interface.new_socket(name="Output", in_out='OUTPUT', socket_type='NodeSocketFloat')
    output_socket.default_value = 0.0
    output_socket.min_value = -3.4028234663852886e+38
    output_socket.max_value = 3.4028234663852886e+38
    output_socket.subtype = 'NONE'
    output_socket.attribute_domain = 'POINT'
    output_socket.default_input = 'VALUE'
    output_socket.structure_type = 'AUTO'

    # Socket Menu
    menu_socket = menu_switching_1.interface.new_socket(name="Menu", in_out='INPUT', socket_type='NodeSocketMenu')
    menu_socket.attribute_domain = 'POINT'
    menu_socket.default_input = 'VALUE'
    menu_socket.structure_type = 'AUTO'
    menu_socket.optional_label = True

    # Socket Frame Index
    frame_index_socket = menu_switching_1.interface.new_socket(name="Frame Index", in_out='INPUT', socket_type='NodeSocketFloat')
    frame_index_socket.default_value = 0.0
    frame_index_socket.min_value = -3.4028234663852886e+38
    frame_index_socket.max_value = 3.4028234663852886e+38
    frame_index_socket.subtype = 'NONE'
    frame_index_socket.attribute_domain = 'POINT'
    frame_index_socket.default_input = 'VALUE'
    frame_index_socket.structure_type = 'AUTO'

    # Socket SRC_Fm
    src_fm_socket = menu_switching_1.interface.new_socket(name="SRC_Fm", in_out='INPUT', socket_type='NodeSocketFloat')
    src_fm_socket.default_value = 0.0
    src_fm_socket.min_value = -3.4028234663852886e+38
    src_fm_socket.max_value = 3.4028234663852886e+38
    src_fm_socket.subtype = 'NONE'
    src_fm_socket.attribute_domain = 'POINT'
    src_fm_socket.default_input = 'VALUE'
    src_fm_socket.structure_type = 'AUTO'

    # Initialize menu_switching_1 nodes

    # Node 组输出
    ___ = menu_switching_1.nodes.new("NodeGroupOutput")
    ___.name = "组输出"
    ___.is_active_output = True

    # Node 组输入
    ____1 = menu_switching_1.nodes.new("NodeGroupInput")
    ____1.name = "组输入"

    # Node Menu Switch
    menu_switch = menu_switching_1.nodes.new("GeometryNodeMenuSwitch")
    menu_switch.name = "Menu Switch"
    menu_switch.active_index = 1
    menu_switch.data_type = 'FLOAT'
    menu_switch.enum_items.clear()
    menu_switch.enum_items.new("Frame Index")
    menu_switch.enum_items[0].description = "Frame Index"
    menu_switch.enum_items.new("SRC_Fm")
    menu_switch.enum_items[1].description = ""

    # Set locations
    menu_switching_1.nodes["组输出"].location = (190.00001525878906, 0.0)
    menu_switching_1.nodes["组输入"].location = (-225.79928588867188, -15.734049797058105)
    menu_switching_1.nodes["Menu Switch"].location = (0.0, 0.0)

    # Set dimensions
    menu_switching_1.nodes["组输出"].width  = 140.0
    menu_switching_1.nodes["组输出"].height = 100.0

    menu_switching_1.nodes["组输入"].width  = 140.0
    menu_switching_1.nodes["组输入"].height = 100.0

    menu_switching_1.nodes["Menu Switch"].width  = 140.0
    menu_switching_1.nodes["Menu Switch"].height = 100.0


    # Initialize menu_switching_1 links

    # ____1.Menu -> menu_switch.Menu
    menu_switching_1.links.new(
        menu_switching_1.nodes["组输入"].outputs[0],
        menu_switching_1.nodes["Menu Switch"].inputs[0]
    )
    # ____1.Frame Index -> menu_switch.Frame Index
    menu_switching_1.links.new(
        menu_switching_1.nodes["组输入"].outputs[1],
        menu_switching_1.nodes["Menu Switch"].inputs[1]
    )
    # menu_switch.Output -> ___.Output
    menu_switching_1.links.new(
        menu_switching_1.nodes["Menu Switch"].outputs[0],
        menu_switching_1.nodes["组输出"].inputs[0]
    )
    # ____1.SRC_Fm -> menu_switch.SRC_Fm
    menu_switching_1.links.new(
        menu_switching_1.nodes["组输入"].outputs[2],
        menu_switching_1.nodes["Menu Switch"].inputs[2]
    )

    return menu_switching_1


def input_method_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize Input Method node group"""
    input_method_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="Input Method")

    input_method_1.color_tag = 'NONE'
    input_method_1.description = ""
    input_method_1.default_group_node_width = 140
    input_method_1.show_modifier_manage_panel = True

    # input_method_1 interface

    # Socket Output
    output_socket = input_method_1.interface.new_socket(name="Output", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    output_socket.attribute_domain = 'POINT'
    output_socket.default_input = 'VALUE'
    output_socket.structure_type = 'AUTO'

    # Socket _4D
    _4d_socket = input_method_1.interface.new_socket(name="_4D", in_out='OUTPUT', socket_type='NodeSocketBool')
    _4d_socket.default_value = False
    _4d_socket.attribute_domain = 'POINT'
    _4d_socket.default_input = 'VALUE'
    _4d_socket.structure_type = 'AUTO'

    # Socket 分段4D
    __4d_socket = input_method_1.interface.new_socket(name="分段4D", in_out='OUTPUT', socket_type='NodeSocketBool')
    __4d_socket.default_value = False
    __4d_socket.attribute_domain = 'POINT'
    __4d_socket.default_input = 'VALUE'
    __4d_socket.structure_type = 'AUTO'

    # Socket Menu
    menu_socket = input_method_1.interface.new_socket(name="Menu", in_out='INPUT', socket_type='NodeSocketMenu')
    menu_socket.attribute_domain = 'POINT'
    menu_socket.default_input = 'VALUE'
    menu_socket.structure_type = 'AUTO'
    menu_socket.optional_label = True

    # Socket 3dgs序列
    _3dgs___socket = input_method_1.interface.new_socket(name="3dgs序列", in_out='INPUT', socket_type='NodeSocketGeometry')
    _3dgs___socket.attribute_domain = 'POINT'
    _3dgs___socket.default_input = 'VALUE'
    _3dgs___socket.structure_type = 'AUTO'

    # Socket 4dgs
    _4dgs_socket = input_method_1.interface.new_socket(name="4dgs", in_out='INPUT', socket_type='NodeSocketGeometry')
    _4dgs_socket.attribute_domain = 'POINT'
    _4dgs_socket.default_input = 'VALUE'
    _4dgs_socket.structure_type = 'AUTO'

    # Socket 分段4dgs
    __4dgs_socket = input_method_1.interface.new_socket(name="分段4dgs", in_out='INPUT', socket_type='NodeSocketGeometry')
    __4dgs_socket.attribute_domain = 'POINT'
    __4dgs_socket.default_input = 'VALUE'
    __4dgs_socket.structure_type = 'AUTO'

    # Initialize input_method_1 nodes

    # Node 组输出
    ___ = input_method_1.nodes.new("NodeGroupOutput")
    ___.name = "组输出"
    ___.is_active_output = True

    # Node 组输入
    ____1 = input_method_1.nodes.new("NodeGroupInput")
    ____1.name = "组输入"

    # Node 菜单切换.001
    _____001 = input_method_1.nodes.new("GeometryNodeMenuSwitch")
    _____001.name = "菜单切换.001"
    _____001.active_index = 2
    _____001.data_type = 'INT'
    _____001.enum_items.clear()
    _____001.enum_items.new("3dgs")
    _____001.enum_items[0].description = ""
    _____001.enum_items.new("4dgs")
    _____001.enum_items[1].description = ""
    _____001.enum_items.new("multi-4dgs")
    _____001.enum_items[2].description = ""
    # Item_0
    _____001.inputs[1].default_value = 0
    # Item_1
    _____001.inputs[2].default_value = 1
    # Item_2
    _____001.inputs[3].default_value = 2

    # Node 编号切换
    ____ = input_method_1.nodes.new("GeometryNodeIndexSwitch")
    ____.name = "编号切换"
    ____.data_type = 'GEOMETRY'
    ____.index_switch_items.clear()
    ____.index_switch_items.new()
    ____.index_switch_items.new()
    ____.index_switch_items.new()

    # Node 比较
    __ = input_method_1.nodes.new("FunctionNodeCompare")
    __.name = "比较"
    __.data_type = 'INT'
    __.mode = 'ELEMENT'
    __.operation = 'EQUAL'
    # B_INT
    __.inputs[3].default_value = 2

    # Node 转接点
    ____2 = input_method_1.nodes.new("NodeReroute")
    ____2.name = "转接点"
    ____2.socket_idname = "NodeSocketInt"
    # Set locations
    input_method_1.nodes["组输出"].location = (707.9984741210938, 182.02783203125)
    input_method_1.nodes["组输入"].location = (-407.6867370605469, -19.80352020263672)
    input_method_1.nodes["菜单切换.001"].location = (-137.109375, 186.37750244140625)
    input_method_1.nodes["编号切换"].location = (149.737060546875, 42.22127914428711)
    input_method_1.nodes["比较"].location = (376.9665832519531, 44.975433349609375)
    input_method_1.nodes["转接点"].location = (393.4061584472656, 136.5274200439453)

    # Set dimensions
    input_method_1.nodes["组输出"].width  = 140.0
    input_method_1.nodes["组输出"].height = 100.0

    input_method_1.nodes["组输入"].width  = 140.0
    input_method_1.nodes["组输入"].height = 100.0

    input_method_1.nodes["菜单切换.001"].width  = 140.0
    input_method_1.nodes["菜单切换.001"].height = 100.0

    input_method_1.nodes["编号切换"].width  = 140.0
    input_method_1.nodes["编号切换"].height = 100.0

    input_method_1.nodes["比较"].width  = 140.0
    input_method_1.nodes["比较"].height = 100.0

    input_method_1.nodes["转接点"].width  = 20.0
    input_method_1.nodes["转接点"].height = 100.0


    # Initialize input_method_1 links

    # ____1.Menu -> _____001.Menu
    input_method_1.links.new(
        input_method_1.nodes["组输入"].outputs[0],
        input_method_1.nodes["菜单切换.001"].inputs[0]
    )
    # _____001.Output -> ____.Index
    input_method_1.links.new(
        input_method_1.nodes["菜单切换.001"].outputs[0],
        input_method_1.nodes["编号切换"].inputs[0]
    )
    # ____1.3dgs序列 -> ____.0
    input_method_1.links.new(
        input_method_1.nodes["组输入"].outputs[1],
        input_method_1.nodes["编号切换"].inputs[1]
    )
    # ____1.4dgs -> ____.1
    input_method_1.links.new(
        input_method_1.nodes["组输入"].outputs[2],
        input_method_1.nodes["编号切换"].inputs[2]
    )
    # ____.Output -> ___.Output
    input_method_1.links.new(
        input_method_1.nodes["编号切换"].outputs[0],
        input_method_1.nodes["组输出"].inputs[0]
    )
    # ____1.分段4dgs -> ____.2
    input_method_1.links.new(
        input_method_1.nodes["组输入"].outputs[3],
        input_method_1.nodes["编号切换"].inputs[3]
    )
    # _____001.Output -> __.A
    input_method_1.links.new(
        input_method_1.nodes["菜单切换.001"].outputs[0],
        input_method_1.nodes["比较"].inputs[2]
    )
    # __.Result -> ___.分段4D
    input_method_1.links.new(
        input_method_1.nodes["比较"].outputs[0],
        input_method_1.nodes["组输出"].inputs[2]
    )
    # _____001.Output -> ____2.Input
    input_method_1.links.new(
        input_method_1.nodes["菜单切换.001"].outputs[0],
        input_method_1.nodes["转接点"].inputs[0]
    )
    # ____2.Output -> ___._4D
    input_method_1.links.new(
        input_method_1.nodes["转接点"].outputs[0],
        input_method_1.nodes["组输出"].inputs[1]
    )
    menu_socket.default_value = '3dgs'

    return input_method_1


def sigmod_g_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize Sigmod_G node group"""
    sigmod_g_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="Sigmod_G")

    sigmod_g_1.color_tag = 'NONE'
    sigmod_g_1.description = ""
    sigmod_g_1.default_group_node_width = 140
    sigmod_g_1.show_modifier_manage_panel = True

    # sigmod_g_1 interface

    # Socket Value
    value_socket = sigmod_g_1.interface.new_socket(name="Value", in_out='OUTPUT', socket_type='NodeSocketFloat')
    value_socket.default_value = 0.0
    value_socket.min_value = -3.4028234663852886e+38
    value_socket.max_value = 3.4028234663852886e+38
    value_socket.subtype = 'NONE'
    value_socket.attribute_domain = 'POINT'
    value_socket.default_input = 'VALUE'
    value_socket.structure_type = 'AUTO'

    # Socket Value
    value_socket_1 = sigmod_g_1.interface.new_socket(name="Value", in_out='INPUT', socket_type='NodeSocketFloat')
    value_socket_1.default_value = 1.0
    value_socket_1.min_value = -10000.0
    value_socket_1.max_value = 10000.0
    value_socket_1.subtype = 'NONE'
    value_socket_1.attribute_domain = 'POINT'
    value_socket_1.default_input = 'VALUE'
    value_socket_1.structure_type = 'AUTO'

    # Socket inv_Opacity
    inv_opacity_socket = sigmod_g_1.interface.new_socket(name="inv_Opacity", in_out='INPUT', socket_type='NodeSocketBool')
    inv_opacity_socket.default_value = False
    inv_opacity_socket.attribute_domain = 'POINT'
    inv_opacity_socket.default_input = 'VALUE'
    inv_opacity_socket.structure_type = 'AUTO'

    # Initialize sigmod_g_1 nodes

    # Node 组输出
    ___ = sigmod_g_1.nodes.new("NodeGroupOutput")
    ___.name = "组输出"
    ___.is_active_output = True

    # Node 组输入
    ____1 = sigmod_g_1.nodes.new("NodeGroupInput")
    ____1.name = "组输入"

    # Node 运算.035
    ___035 = sigmod_g_1.nodes.new("ShaderNodeMath")
    ___035.name = "运算.035"
    ___035.operation = 'DIVIDE'
    ___035.use_clamp = False
    # Value
    ___035.inputs[0].default_value = 1.0

    # Node 运算.036
    ___036 = sigmod_g_1.nodes.new("ShaderNodeMath")
    ___036.name = "运算.036"
    ___036.operation = 'ADD'
    ___036.use_clamp = False
    # Value
    ___036.inputs[0].default_value = 1.0

    # Node 运算.037
    ___037 = sigmod_g_1.nodes.new("ShaderNodeMath")
    ___037.name = "运算.037"
    ___037.operation = 'EXPONENT'
    ___037.use_clamp = False

    # Node 运算.038
    ___038 = sigmod_g_1.nodes.new("ShaderNodeMath")
    ___038.name = "运算.038"
    ___038.operation = 'MULTIPLY'
    ___038.use_clamp = False
    # Value_001
    ___038.inputs[1].default_value = -1.0

    # Node 切换
    __ = sigmod_g_1.nodes.new("GeometryNodeSwitch")
    __.name = "切换"
    __.input_type = 'FLOAT'

    # Set locations
    sigmod_g_1.nodes["组输出"].location = (544.001708984375, 0.0)
    sigmod_g_1.nodes["组输入"].location = (-625.1428833007812, -61.714237213134766)
    sigmod_g_1.nodes["运算.035"].location = (354.001708984375, 91.33685302734375)
    sigmod_g_1.nodes["运算.036"].location = (278.571044921875, -76.21893310546875)
    sigmod_g_1.nodes["运算.037"].location = (89.9954833984375, -91.33685302734375)
    sigmod_g_1.nodes["运算.038"].location = (-348.0893249511719, -174.00128173828125)
    sigmod_g_1.nodes["切换"].location = (-119.42047119140625, -52.69608688354492)

    # Set dimensions
    sigmod_g_1.nodes["组输出"].width  = 140.0
    sigmod_g_1.nodes["组输出"].height = 100.0

    sigmod_g_1.nodes["组输入"].width  = 140.0
    sigmod_g_1.nodes["组输入"].height = 100.0

    sigmod_g_1.nodes["运算.035"].width  = 140.0
    sigmod_g_1.nodes["运算.035"].height = 100.0

    sigmod_g_1.nodes["运算.036"].width  = 140.0
    sigmod_g_1.nodes["运算.036"].height = 100.0

    sigmod_g_1.nodes["运算.037"].width  = 140.0
    sigmod_g_1.nodes["运算.037"].height = 100.0

    sigmod_g_1.nodes["运算.038"].width  = 140.0
    sigmod_g_1.nodes["运算.038"].height = 100.0

    sigmod_g_1.nodes["切换"].width  = 140.0
    sigmod_g_1.nodes["切换"].height = 100.0


    # Initialize sigmod_g_1 links

    # ___036.Value -> ___035.Value
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["运算.036"].outputs[0],
        sigmod_g_1.nodes["运算.035"].inputs[1]
    )
    # ___037.Value -> ___036.Value
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["运算.037"].outputs[0],
        sigmod_g_1.nodes["运算.036"].inputs[1]
    )
    # __.Output -> ___037.Value
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["切换"].outputs[0],
        sigmod_g_1.nodes["运算.037"].inputs[0]
    )
    # ____1.Value -> ___038.Value
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["组输入"].outputs[0],
        sigmod_g_1.nodes["运算.038"].inputs[0]
    )
    # ___035.Value -> ___.Value
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["运算.035"].outputs[0],
        sigmod_g_1.nodes["组输出"].inputs[0]
    )
    # ____1.inv_Opacity -> __.Switch
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["组输入"].outputs[1],
        sigmod_g_1.nodes["切换"].inputs[0]
    )
    # ___038.Value -> __.False
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["运算.038"].outputs[0],
        sigmod_g_1.nodes["切换"].inputs[1]
    )
    # ____1.Value -> __.True
    sigmod_g_1.links.new(
        sigmod_g_1.nodes["组输入"].outputs[0],
        sigmod_g_1.nodes["切换"].inputs[2]
    )

    return sigmod_g_1


def sh_g_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize SH_G node group"""
    sh_g_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="SH_G")

    sh_g_1.color_tag = 'NONE'
    sh_g_1.description = ""
    sh_g_1.default_group_node_width = 140
    sh_g_1.show_modifier_manage_panel = True

    # sh_g_1 interface

    # Socket X
    x_socket = sh_g_1.interface.new_socket(name="X", in_out='OUTPUT', socket_type='NodeSocketFloat')
    x_socket.default_value = 0.0
    x_socket.min_value = -3.4028234663852886e+38
    x_socket.max_value = 3.4028234663852886e+38
    x_socket.subtype = 'NONE'
    x_socket.attribute_domain = 'POINT'
    x_socket.default_input = 'VALUE'
    x_socket.structure_type = 'AUTO'

    # Socket Y
    y_socket = sh_g_1.interface.new_socket(name="Y", in_out='OUTPUT', socket_type='NodeSocketFloat')
    y_socket.default_value = 0.0
    y_socket.min_value = -3.4028234663852886e+38
    y_socket.max_value = 3.4028234663852886e+38
    y_socket.subtype = 'NONE'
    y_socket.attribute_domain = 'POINT'
    y_socket.default_input = 'VALUE'
    y_socket.structure_type = 'AUTO'

    # Socket Z
    z_socket = sh_g_1.interface.new_socket(name="Z", in_out='OUTPUT', socket_type='NodeSocketFloat')
    z_socket.default_value = 0.0
    z_socket.min_value = -3.4028234663852886e+38
    z_socket.max_value = 3.4028234663852886e+38
    z_socket.subtype = 'NONE'
    z_socket.attribute_domain = 'POINT'
    z_socket.default_input = 'VALUE'
    z_socket.structure_type = 'AUTO'

    # Socket xx
    xx_socket = sh_g_1.interface.new_socket(name="xx", in_out='OUTPUT', socket_type='NodeSocketFloat')
    xx_socket.default_value = 0.0
    xx_socket.min_value = -3.4028234663852886e+38
    xx_socket.max_value = 3.4028234663852886e+38
    xx_socket.subtype = 'NONE'
    xx_socket.attribute_domain = 'POINT'
    xx_socket.default_input = 'VALUE'
    xx_socket.structure_type = 'AUTO'

    # Socket yy
    yy_socket = sh_g_1.interface.new_socket(name="yy", in_out='OUTPUT', socket_type='NodeSocketFloat')
    yy_socket.default_value = 0.0
    yy_socket.min_value = -3.4028234663852886e+38
    yy_socket.max_value = 3.4028234663852886e+38
    yy_socket.subtype = 'NONE'
    yy_socket.attribute_domain = 'POINT'
    yy_socket.default_input = 'VALUE'
    yy_socket.structure_type = 'AUTO'

    # Socket zz
    zz_socket = sh_g_1.interface.new_socket(name="zz", in_out='OUTPUT', socket_type='NodeSocketFloat')
    zz_socket.default_value = 0.0
    zz_socket.min_value = -3.4028234663852886e+38
    zz_socket.max_value = 3.4028234663852886e+38
    zz_socket.subtype = 'NONE'
    zz_socket.attribute_domain = 'POINT'
    zz_socket.default_input = 'VALUE'
    zz_socket.structure_type = 'AUTO'

    # Socket xy
    xy_socket = sh_g_1.interface.new_socket(name="xy", in_out='OUTPUT', socket_type='NodeSocketFloat')
    xy_socket.default_value = 0.0
    xy_socket.min_value = -3.4028234663852886e+38
    xy_socket.max_value = 3.4028234663852886e+38
    xy_socket.subtype = 'NONE'
    xy_socket.attribute_domain = 'POINT'
    xy_socket.default_input = 'VALUE'
    xy_socket.structure_type = 'AUTO'

    # Socket yz
    yz_socket = sh_g_1.interface.new_socket(name="yz", in_out='OUTPUT', socket_type='NodeSocketFloat')
    yz_socket.default_value = 0.0
    yz_socket.min_value = -3.4028234663852886e+38
    yz_socket.max_value = 3.4028234663852886e+38
    yz_socket.subtype = 'NONE'
    yz_socket.attribute_domain = 'POINT'
    yz_socket.default_input = 'VALUE'
    yz_socket.structure_type = 'AUTO'

    # Socket xz
    xz_socket = sh_g_1.interface.new_socket(name="xz", in_out='OUTPUT', socket_type='NodeSocketFloat')
    xz_socket.default_value = 0.0
    xz_socket.min_value = -3.4028234663852886e+38
    xz_socket.max_value = 3.4028234663852886e+38
    xz_socket.subtype = 'NONE'
    xz_socket.attribute_domain = 'POINT'
    xz_socket.default_input = 'VALUE'
    xz_socket.structure_type = 'AUTO'

    # Socket Vector
    vector_socket = sh_g_1.interface.new_socket(name="Vector", in_out='OUTPUT', socket_type='NodeSocketVector')
    vector_socket.default_value = (0.0, 0.0, 0.0)
    vector_socket.min_value = -3.4028234663852886e+38
    vector_socket.max_value = 3.4028234663852886e+38
    vector_socket.subtype = 'NONE'
    vector_socket.attribute_domain = 'POINT'
    vector_socket.default_input = 'VALUE'
    vector_socket.structure_type = 'AUTO'

    # Socket Rotation
    rotation_socket = sh_g_1.interface.new_socket(name="Rotation", in_out='OUTPUT', socket_type='NodeSocketRotation')
    rotation_socket.default_value = (0.0, 0.0, 0.0)
    rotation_socket.attribute_domain = 'POINT'
    rotation_socket.default_input = 'VALUE'
    rotation_socket.structure_type = 'AUTO'

    # Initialize sh_g_1 nodes

    # Node 组输出
    ___ = sh_g_1.nodes.new("NodeGroupOutput")
    ___.name = "组输出"
    ___.is_active_output = True

    # Node 分离 XYZ.002
    ___xyz_002 = sh_g_1.nodes.new("ShaderNodeSeparateXYZ")
    ___xyz_002.name = "分离 XYZ.002"

    # Node 运算.086
    ___086 = sh_g_1.nodes.new("ShaderNodeMath")
    ___086.name = "运算.086"
    ___086.hide = True
    ___086.operation = 'MULTIPLY'
    ___086.use_clamp = False

    # Node 运算.087
    ___087 = sh_g_1.nodes.new("ShaderNodeMath")
    ___087.name = "运算.087"
    ___087.hide = True
    ___087.operation = 'MULTIPLY'
    ___087.use_clamp = False

    # Node 运算.088
    ___088 = sh_g_1.nodes.new("ShaderNodeMath")
    ___088.name = "运算.088"
    ___088.hide = True
    ___088.operation = 'MULTIPLY'
    ___088.use_clamp = False

    # Node 运算.089
    ___089 = sh_g_1.nodes.new("ShaderNodeMath")
    ___089.name = "运算.089"
    ___089.hide = True
    ___089.operation = 'MULTIPLY'
    ___089.use_clamp = False

    # Node 运算.090
    ___090 = sh_g_1.nodes.new("ShaderNodeMath")
    ___090.name = "运算.090"
    ___090.hide = True
    ___090.operation = 'MULTIPLY'
    ___090.use_clamp = False

    # Node 运算.091
    ___091 = sh_g_1.nodes.new("ShaderNodeMath")
    ___091.name = "运算.091"
    ___091.hide = True
    ___091.operation = 'MULTIPLY'
    ___091.use_clamp = False

    # Node 矢量旋转.001
    _____001 = sh_g_1.nodes.new("ShaderNodeVectorRotate")
    _____001.name = "矢量旋转.001"
    _____001.invert = True
    _____001.rotation_type = 'EULER_XYZ'
    _____001.inputs[1].hide = True
    _____001.inputs[2].hide = True
    _____001.inputs[3].hide = True
    # Center
    _____001.inputs[1].default_value = (0.0, 0.0, 0.0)

    # Node 物体信息.007
    _____007 = sh_g_1.nodes.new("GeometryNodeObjectInfo")
    _____007.name = "物体信息.007"
    _____007.transform_space = 'ORIGINAL'
    _____007.inputs[1].hide = True
    _____007.outputs[0].hide = True
    _____007.outputs[1].hide = True
    _____007.outputs[3].hide = True
    _____007.outputs[4].hide = True
    # As Instance
    _____007.inputs[1].default_value = False

    # Node 自身物体
    ____ = sh_g_1.nodes.new("GeometryNodeSelfObject")
    ____.name = "自身物体"

    # Node 自身物体.001
    _____001_1 = sh_g_1.nodes.new("GeometryNodeSelfObject")
    _____001_1.name = "自身物体.001"

    # Node 物体信息.008
    _____008 = sh_g_1.nodes.new("GeometryNodeObjectInfo")
    _____008.name = "物体信息.008"
    _____008.transform_space = 'ORIGINAL'
    # As Instance
    _____008.inputs[1].default_value = False

    # Node 活动摄像机.004
    ______004 = sh_g_1.nodes.new("GeometryNodeInputActiveCamera")
    ______004.name = "活动摄像机.004"

    # Node 物体信息.009
    _____009 = sh_g_1.nodes.new("GeometryNodeObjectInfo")
    _____009.name = "物体信息.009"
    _____009.transform_space = 'ORIGINAL'
    # As Instance
    _____009.inputs[1].default_value = False

    # Node 矢量运算.025
    _____025 = sh_g_1.nodes.new("ShaderNodeVectorMath")
    _____025.name = "矢量运算.025"
    _____025.operation = 'SUBTRACT'

    # Node 矢量运算.026
    _____026 = sh_g_1.nodes.new("ShaderNodeVectorMath")
    _____026.name = "矢量运算.026"
    _____026.operation = 'NORMALIZE'

    # Node 位置.003
    ___003 = sh_g_1.nodes.new("GeometryNodeInputPosition")
    ___003.name = "位置.003"

    # Node 投影点.001
    ____001 = sh_g_1.nodes.new("FunctionNodeProjectPoint")
    ____001.name = "投影点.001"

    # Node 已命名属性
    _____ = sh_g_1.nodes.new("GeometryNodeInputNamedAttribute")
    _____.name = "已命名属性"
    _____.data_type = 'FLOAT_VECTOR'
    # Name
    _____.inputs[0].default_value = "PPP"

    # Node 已命名属性.001
    ______001 = sh_g_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______001.name = "已命名属性.001"
    ______001.data_type = 'FLOAT_VECTOR'
    # Name
    ______001.inputs[0].default_value = "G_Rot"

    # Node 法向
    __ = sh_g_1.nodes.new("GeometryNodeInputNormal")
    __.name = "法向"
    __.legacy_corner_normals = False
    __.outputs[1].hide = True

    # Set locations
    sh_g_1.nodes["组输出"].location = (1086.172119140625, 180.9743194580078)
    sh_g_1.nodes["分离 XYZ.002"].location = (509.8641357421875, 128.1640625)
    sh_g_1.nodes["运算.086"].location = (849.0804443359375, 130.257568359375)
    sh_g_1.nodes["运算.087"].location = (840.5623779296875, 86.506591796875)
    sh_g_1.nodes["运算.088"].location = (830.2366943359375, 45.55517578125)
    sh_g_1.nodes["运算.089"].location = (802.3702392578125, -43.128173828125)
    sh_g_1.nodes["运算.090"].location = (814.9122314453125, 0.62060546875)
    sh_g_1.nodes["运算.091"].location = (794.6021728515625, -87.43994140625)
    sh_g_1.nodes["矢量旋转.001"].location = (161.0282745361328, 126.39219665527344)
    sh_g_1.nodes["物体信息.007"].location = (-229.52798461914062, -24.023345947265625)
    sh_g_1.nodes["自身物体"].location = (-445.3629455566406, -125.95022583007812)
    sh_g_1.nodes["自身物体.001"].location = (-1109.625244140625, 323.2443542480469)
    sh_g_1.nodes["物体信息.008"].location = (-940.11572265625, 469.47784423828125)
    sh_g_1.nodes["活动摄像机.004"].location = (-916.6373291015625, -43.87701416015625)
    sh_g_1.nodes["物体信息.009"].location = (-756.7252197265625, -43.87652587890625)
    sh_g_1.nodes["矢量运算.025"].location = (-570.9656372070312, 96.16282653808594)
    sh_g_1.nodes["矢量运算.026"].location = (-343.9449768066406, 138.86346435546875)
    sh_g_1.nodes["位置.003"].location = (-948.2464599609375, 234.90756225585938)
    sh_g_1.nodes["投影点.001"].location = (-747.0286865234375, 233.15841674804688)
    sh_g_1.nodes["已命名属性"].location = (-760.392333984375, 126.20558166503906)
    sh_g_1.nodes["已命名属性.001"].location = (-7.0997467041015625, -128.5899658203125)
    sh_g_1.nodes["法向"].location = (-569.7020874023438, 182.59640502929688)

    # Set dimensions
    sh_g_1.nodes["组输出"].width  = 140.0
    sh_g_1.nodes["组输出"].height = 100.0

    sh_g_1.nodes["分离 XYZ.002"].width  = 140.0
    sh_g_1.nodes["分离 XYZ.002"].height = 100.0

    sh_g_1.nodes["运算.086"].width  = 140.0
    sh_g_1.nodes["运算.086"].height = 100.0

    sh_g_1.nodes["运算.087"].width  = 140.0
    sh_g_1.nodes["运算.087"].height = 100.0

    sh_g_1.nodes["运算.088"].width  = 140.0
    sh_g_1.nodes["运算.088"].height = 100.0

    sh_g_1.nodes["运算.089"].width  = 140.0
    sh_g_1.nodes["运算.089"].height = 100.0

    sh_g_1.nodes["运算.090"].width  = 140.0
    sh_g_1.nodes["运算.090"].height = 100.0

    sh_g_1.nodes["运算.091"].width  = 140.0
    sh_g_1.nodes["运算.091"].height = 100.0

    sh_g_1.nodes["矢量旋转.001"].width  = 140.0
    sh_g_1.nodes["矢量旋转.001"].height = 100.0

    sh_g_1.nodes["物体信息.007"].width  = 140.0
    sh_g_1.nodes["物体信息.007"].height = 100.0

    sh_g_1.nodes["自身物体"].width  = 140.0
    sh_g_1.nodes["自身物体"].height = 100.0

    sh_g_1.nodes["自身物体.001"].width  = 140.0
    sh_g_1.nodes["自身物体.001"].height = 100.0

    sh_g_1.nodes["物体信息.008"].width  = 140.0
    sh_g_1.nodes["物体信息.008"].height = 100.0

    sh_g_1.nodes["活动摄像机.004"].width  = 140.0
    sh_g_1.nodes["活动摄像机.004"].height = 100.0

    sh_g_1.nodes["物体信息.009"].width  = 140.0
    sh_g_1.nodes["物体信息.009"].height = 100.0

    sh_g_1.nodes["矢量运算.025"].width  = 140.0
    sh_g_1.nodes["矢量运算.025"].height = 100.0

    sh_g_1.nodes["矢量运算.026"].width  = 140.0
    sh_g_1.nodes["矢量运算.026"].height = 100.0

    sh_g_1.nodes["位置.003"].width  = 140.0
    sh_g_1.nodes["位置.003"].height = 100.0

    sh_g_1.nodes["投影点.001"].width  = 140.0
    sh_g_1.nodes["投影点.001"].height = 100.0

    sh_g_1.nodes["已命名属性"].width  = 140.0
    sh_g_1.nodes["已命名属性"].height = 100.0

    sh_g_1.nodes["已命名属性.001"].width  = 140.0
    sh_g_1.nodes["已命名属性.001"].height = 100.0

    sh_g_1.nodes["法向"].width  = 140.0
    sh_g_1.nodes["法向"].height = 100.0


    # Initialize sh_g_1 links

    # ___xyz_002.Y -> ___089.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[1],
        sh_g_1.nodes["运算.089"].inputs[0]
    )
    # ___xyz_002.X -> ___086.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[0],
        sh_g_1.nodes["运算.086"].inputs[0]
    )
    # ___xyz_002.X -> ___086.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[0],
        sh_g_1.nodes["运算.086"].inputs[1]
    )
    # ___xyz_002.Z -> ___089.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[2],
        sh_g_1.nodes["运算.089"].inputs[1]
    )
    # ___xyz_002.Z -> ___088.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[2],
        sh_g_1.nodes["运算.088"].inputs[0]
    )
    # ___xyz_002.Y -> ___087.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[1],
        sh_g_1.nodes["运算.087"].inputs[1]
    )
    # ___xyz_002.X -> ___090.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[0],
        sh_g_1.nodes["运算.090"].inputs[0]
    )
    # ___xyz_002.X -> ___091.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[0],
        sh_g_1.nodes["运算.091"].inputs[1]
    )
    # ___xyz_002.Y -> ___087.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[1],
        sh_g_1.nodes["运算.087"].inputs[0]
    )
    # ___xyz_002.Y -> ___090.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[1],
        sh_g_1.nodes["运算.090"].inputs[1]
    )
    # ___xyz_002.Z -> ___088.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[2],
        sh_g_1.nodes["运算.088"].inputs[1]
    )
    # ___xyz_002.Z -> ___091.Value
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[2],
        sh_g_1.nodes["运算.091"].inputs[0]
    )
    # ___xyz_002.X -> ___.X
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[0]
    )
    # ___xyz_002.Y -> ___.Y
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[1],
        sh_g_1.nodes["组输出"].inputs[1]
    )
    # ___xyz_002.Z -> ___.Z
    sh_g_1.links.new(
        sh_g_1.nodes["分离 XYZ.002"].outputs[2],
        sh_g_1.nodes["组输出"].inputs[2]
    )
    # ___086.Value -> ___.xx
    sh_g_1.links.new(
        sh_g_1.nodes["运算.086"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[3]
    )
    # ___087.Value -> ___.yy
    sh_g_1.links.new(
        sh_g_1.nodes["运算.087"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[4]
    )
    # ___088.Value -> ___.zz
    sh_g_1.links.new(
        sh_g_1.nodes["运算.088"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[5]
    )
    # ___090.Value -> ___.xy
    sh_g_1.links.new(
        sh_g_1.nodes["运算.090"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[6]
    )
    # ___089.Value -> ___.yz
    sh_g_1.links.new(
        sh_g_1.nodes["运算.089"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[7]
    )
    # ___091.Value -> ___.xz
    sh_g_1.links.new(
        sh_g_1.nodes["运算.091"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[8]
    )
    # ____.Self Object -> _____007.Object
    sh_g_1.links.new(
        sh_g_1.nodes["自身物体"].outputs[0],
        sh_g_1.nodes["物体信息.007"].inputs[0]
    )
    # _____001_1.Self Object -> _____008.Object
    sh_g_1.links.new(
        sh_g_1.nodes["自身物体.001"].outputs[0],
        sh_g_1.nodes["物体信息.008"].inputs[0]
    )
    # ______004.Active Camera -> _____009.Object
    sh_g_1.links.new(
        sh_g_1.nodes["活动摄像机.004"].outputs[0],
        sh_g_1.nodes["物体信息.009"].inputs[0]
    )
    # _____008.Transform -> ____001.Transform
    sh_g_1.links.new(
        sh_g_1.nodes["物体信息.008"].outputs[0],
        sh_g_1.nodes["投影点.001"].inputs[1]
    )
    # _____007.Rotation -> _____001.Rotation
    sh_g_1.links.new(
        sh_g_1.nodes["物体信息.007"].outputs[2],
        sh_g_1.nodes["矢量旋转.001"].inputs[4]
    )
    # _____007.Rotation -> ___.Rotation
    sh_g_1.links.new(
        sh_g_1.nodes["物体信息.007"].outputs[2],
        sh_g_1.nodes["组输出"].inputs[10]
    )
    # _____026.Vector -> _____001.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["矢量运算.026"].outputs[0],
        sh_g_1.nodes["矢量旋转.001"].inputs[0]
    )
    # _____001.Vector -> ___xyz_002.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["矢量旋转.001"].outputs[0],
        sh_g_1.nodes["分离 XYZ.002"].inputs[0]
    )
    # _____009.Location -> _____025.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["物体信息.009"].outputs[1],
        sh_g_1.nodes["矢量运算.025"].inputs[1]
    )
    # _____001.Vector -> ___.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["矢量旋转.001"].outputs[0],
        sh_g_1.nodes["组输出"].inputs[9]
    )
    # ___003.Position -> ____001.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["位置.003"].outputs[0],
        sh_g_1.nodes["投影点.001"].inputs[0]
    )
    # _____.Attribute -> _____025.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["已命名属性"].outputs[0],
        sh_g_1.nodes["矢量运算.025"].inputs[0]
    )
    # _____025.Vector -> _____026.Vector
    sh_g_1.links.new(
        sh_g_1.nodes["矢量运算.025"].outputs[0],
        sh_g_1.nodes["矢量运算.026"].inputs[0]
    )

    return sh_g_1


def ugrs_mainnodetree_v1_0_1_node_group(node_tree_names: dict[typing.Callable, str]):
    """Initialize UGRS_MainNodeTree_v1.0 node group"""
    ugrs_mainnodetree_v1_0_1 = bpy.data.node_groups.new(type='GeometryNodeTree', name="UGRS_MainNodeTree_v1.0")

    ugrs_mainnodetree_v1_0_1.color_tag = 'NONE'
    ugrs_mainnodetree_v1_0_1.description = "error"
    ugrs_mainnodetree_v1_0_1.default_group_node_width = 700
    ugrs_mainnodetree_v1_0_1.show_modifier_manage_panel = True

    # ugrs_mainnodetree_v1_0_1 interface

    # Socket Geometry
    geometry_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    geometry_socket.attribute_domain = 'POINT'
    geometry_socket.default_input = 'VALUE'
    geometry_socket.structure_type = 'AUTO'

    # Socket HDR
    hdr_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="HDR", in_out='INPUT', socket_type='NodeSocketMenu')
    hdr_socket.attribute_domain = 'POINT'
    hdr_socket.default_input = 'VALUE'
    hdr_socket.menu_expanded = True
    hdr_socket.structure_type = 'AUTO'

    # Panel Clip
    clip_panel = ugrs_mainnodetree_v1_0_1.interface.new_panel("Clip")
    # Socket object_clip
    object_clip_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="object_clip", in_out='INPUT', socket_type='NodeSocketBool', parent = clip_panel)
    object_clip_socket.default_value = False
    object_clip_socket.attribute_domain = 'POINT'
    object_clip_socket.default_input = 'VALUE'
    object_clip_socket.structure_type = 'AUTO'

    # Socket view_clip
    view_clip_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="view_clip", in_out='INPUT', socket_type='NodeSocketBool', parent = clip_panel)
    view_clip_socket.default_value = True
    view_clip_socket.attribute_domain = 'POINT'
    view_clip_socket.default_input = 'VALUE'
    view_clip_socket.structure_type = 'AUTO'

    # Socket clipArea
    cliparea_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="clipArea", in_out='INPUT', socket_type='NodeSocketObject', parent = clip_panel)
    cliparea_socket.attribute_domain = 'POINT'
    cliparea_socket.default_input = 'VALUE'
    cliparea_socket.structure_type = 'AUTO'


    # Panel Input
    input_panel = ugrs_mainnodetree_v1_0_1.interface.new_panel("Input")
    # Socket Input format
    input_format_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Input format", in_out='INPUT', socket_type='NodeSocketMenu', parent = input_panel)
    input_format_socket.attribute_domain = 'POINT'
    input_format_socket.default_input = 'VALUE'
    input_format_socket.menu_expanded = True
    input_format_socket.structure_type = 'AUTO'

    # Socket 3DGS
    _3dgs_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="3DGS", in_out='INPUT', socket_type='NodeSocketCollection', parent = input_panel)
    _3dgs_socket.attribute_domain = 'POINT'
    _3dgs_socket.default_input = 'VALUE'
    _3dgs_socket.structure_type = 'AUTO'

    # Socket 4DGS
    _4dgs_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="4DGS", in_out='INPUT', socket_type='NodeSocketObject', parent = input_panel)
    _4dgs_socket.attribute_domain = 'POINT'
    _4dgs_socket.default_input = 'VALUE'
    _4dgs_socket.structure_type = 'AUTO'

    # Socket multi4DGS
    multi4dgs_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="multi4DGS", in_out='INPUT', socket_type='NodeSocketCollection', parent = input_panel)
    multi4dgs_socket.attribute_domain = 'POINT'
    multi4dgs_socket.default_input = 'VALUE'
    multi4dgs_socket.structure_type = 'AUTO'

    # Socket FrameCount
    framecount_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="FrameCount", in_out='INPUT', socket_type='NodeSocketFloat', parent = input_panel)
    framecount_socket.default_value = 300.0
    framecount_socket.min_value = 1.0
    framecount_socket.max_value = 10000.0
    framecount_socket.subtype = 'NONE'
    framecount_socket.attribute_domain = 'POINT'
    framecount_socket.default_input = 'VALUE'
    framecount_socket.structure_type = 'AUTO'

    # Socket Source FPS
    source_fps_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Source FPS", in_out='INPUT', socket_type='NodeSocketFloat', parent = input_panel)
    source_fps_socket.default_value = 60.0
    source_fps_socket.min_value = 60.0
    source_fps_socket.max_value = 60.0
    source_fps_socket.subtype = 'NONE'
    source_fps_socket.attribute_domain = 'POINT'
    source_fps_socket.default_input = 'VALUE'
    source_fps_socket.structure_type = 'AUTO'

    # Socket Point Radius
    point_radius_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Point Radius", in_out='INPUT', socket_type='NodeSocketFloat', parent = input_panel)
    point_radius_socket.default_value = 1.0
    point_radius_socket.min_value = 0.0010000000474974513
    point_radius_socket.max_value = 10.0
    point_radius_socket.subtype = 'NONE'
    point_radius_socket.attribute_domain = 'POINT'
    point_radius_socket.default_input = 'VALUE'
    point_radius_socket.structure_type = 'AUTO'

    # Socket inv_Opacity
    inv_opacity_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="inv_Opacity", in_out='INPUT', socket_type='NodeSocketBool', parent = input_panel)
    inv_opacity_socket.default_value = False
    inv_opacity_socket.attribute_domain = 'POINT'
    inv_opacity_socket.default_input = 'VALUE'
    inv_opacity_socket.structure_type = 'AUTO'

    # Socket ColorFormat
    colorformat_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="ColorFormat", in_out='INPUT', socket_type='NodeSocketMenu', parent = input_panel)
    colorformat_socket.attribute_domain = 'POINT'
    colorformat_socket.default_input = 'VALUE'
    colorformat_socket.menu_expanded = True
    colorformat_socket.structure_type = 'AUTO'

    # Socket SHFormat
    shformat_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="SHFormat", in_out='INPUT', socket_type='NodeSocketInt', parent = input_panel)
    shformat_socket.default_value = 3
    shformat_socket.min_value = 0
    shformat_socket.max_value = 3
    shformat_socket.subtype = 'NONE'
    shformat_socket.attribute_domain = 'POINT'
    shformat_socket.default_input = 'VALUE'
    shformat_socket.structure_type = 'AUTO'


    # Panel Frame Control
    frame_control_panel = ugrs_mainnodetree_v1_0_1.interface.new_panel("Frame Control")
    # Socket Control Method
    control_method_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Control Method", in_out='INPUT', socket_type='NodeSocketMenu', parent = frame_control_panel)
    control_method_socket.attribute_domain = 'POINT'
    control_method_socket.default_input = 'VALUE'
    control_method_socket.structure_type = 'AUTO'
    control_method_socket.optional_label = True

    # Socket SRC Fm Start
    src_fm_start_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="SRC Fm Start", in_out='INPUT', socket_type='NodeSocketInt', parent = frame_control_panel)
    src_fm_start_socket.default_value = 0
    src_fm_start_socket.min_value = 0
    src_fm_start_socket.max_value = 2147483647
    src_fm_start_socket.subtype = 'NONE'
    src_fm_start_socket.attribute_domain = 'POINT'
    src_fm_start_socket.default_input = 'VALUE'
    src_fm_start_socket.structure_type = 'AUTO'

    # Socket ClipOfffset
    clipofffset_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="ClipOfffset", in_out='INPUT', socket_type='NodeSocketInt', parent = frame_control_panel)
    clipofffset_socket.default_value = 0
    clipofffset_socket.min_value = -2147483648
    clipofffset_socket.max_value = 2147483647
    clipofffset_socket.subtype = 'NONE'
    clipofffset_socket.attribute_domain = 'POINT'
    clipofffset_socket.default_input = 'VALUE'
    clipofffset_socket.structure_type = 'AUTO'

    # Socket FrameOffset
    frameoffset_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="FrameOffset", in_out='INPUT', socket_type='NodeSocketMenu', parent = frame_control_panel)
    frameoffset_socket.attribute_domain = 'POINT'
    frameoffset_socket.default_input = 'VALUE'
    frameoffset_socket.menu_expanded = True
    frameoffset_socket.structure_type = 'AUTO'

    # Socket Offset
    offset_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Offset", in_out='INPUT', socket_type='NodeSocketFloat', parent = frame_control_panel)
    offset_socket.default_value = 0.0
    offset_socket.min_value = -10000.0
    offset_socket.max_value = 10000.0
    offset_socket.subtype = 'NONE'
    offset_socket.attribute_domain = 'POINT'
    offset_socket.default_input = 'VALUE'
    offset_socket.structure_type = 'AUTO'

    # Socket Frame_Index_input
    frame_index_input_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Frame_Index_input", in_out='INPUT', socket_type='NodeSocketFloat', parent = frame_control_panel)
    frame_index_input_socket.default_value = 1.0
    frame_index_input_socket.min_value = 1.0
    frame_index_input_socket.max_value = 300.0
    frame_index_input_socket.subtype = 'NONE'
    frame_index_input_socket.attribute_domain = 'POINT'
    frame_index_input_socket.default_input = 'VALUE'
    frame_index_input_socket.structure_type = 'AUTO'


    # Panel Geometry
    geometry_panel = ugrs_mainnodetree_v1_0_1.interface.new_panel("Geometry")
    # Socket Geo_Size
    geo_size_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Geo_Size", in_out='INPUT', socket_type='NodeSocketFloat', parent = geometry_panel)
    geo_size_socket.default_value = 3.0
    geo_size_socket.min_value = 0.0
    geo_size_socket.max_value = 8.0
    geo_size_socket.subtype = 'NONE'
    geo_size_socket.attribute_domain = 'POINT'
    geo_size_socket.default_input = 'VALUE'
    geo_size_socket.structure_type = 'AUTO'

    # Socket Display Mode
    display_mode_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Display Mode", in_out='INPUT', socket_type='NodeSocketMenu', parent = geometry_panel)
    display_mode_socket.attribute_domain = 'POINT'
    display_mode_socket.default_input = 'VALUE'
    display_mode_socket.menu_expanded = True
    display_mode_socket.structure_type = 'AUTO'

    # Socket GaussionMode
    gaussionmode_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="GaussionMode", in_out='INPUT', socket_type='NodeSocketMenu', parent = geometry_panel)
    gaussionmode_socket.attribute_domain = 'POINT'
    gaussionmode_socket.default_input = 'VALUE'
    gaussionmode_socket.menu_expanded = True
    gaussionmode_socket.structure_type = 'AUTO'

    # Socket Mesh
    mesh_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Mesh", in_out='INPUT', socket_type='NodeSocketMenu', parent = geometry_panel)
    mesh_socket.attribute_domain = 'POINT'
    mesh_socket.default_input = 'VALUE'
    mesh_socket.structure_type = 'AUTO'

    # Socket edges
    edges_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="edges", in_out='INPUT', socket_type='NodeSocketInt', parent = geometry_panel)
    edges_socket.default_value = 4
    edges_socket.min_value = 3
    edges_socket.max_value = 8
    edges_socket.subtype = 'NONE'
    edges_socket.attribute_domain = 'POINT'
    edges_socket.default_input = 'VALUE'
    edges_socket.structure_type = 'AUTO'

    # Socket AlphaClipMode
    alphaclipmode_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="AlphaClipMode", in_out='INPUT', socket_type='NodeSocketMenu', parent = geometry_panel)
    alphaclipmode_socket.attribute_domain = 'POINT'
    alphaclipmode_socket.default_input = 'VALUE'
    alphaclipmode_socket.menu_expanded = True
    alphaclipmode_socket.structure_type = 'AUTO'

    # Socket PreAlphaClip_Value
    prealphaclip_value_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="PreAlphaClip_Value", in_out='INPUT', socket_type='NodeSocketFloat', parent = geometry_panel)
    prealphaclip_value_socket.default_value = 0.05000000074505806
    prealphaclip_value_socket.min_value = 0.0
    prealphaclip_value_socket.max_value = 1.0
    prealphaclip_value_socket.subtype = 'NONE'
    prealphaclip_value_socket.attribute_domain = 'POINT'
    prealphaclip_value_socket.default_input = 'VALUE'
    prealphaclip_value_socket.structure_type = 'AUTO'

    # Socket PointScale
    pointscale_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="PointScale", in_out='INPUT', socket_type='NodeSocketMenu', parent = geometry_panel)
    pointscale_socket.attribute_domain = 'POINT'
    pointscale_socket.default_input = 'VALUE'
    pointscale_socket.structure_type = 'AUTO'

    # Socket mirrow
    mirrow_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="mirrow", in_out='INPUT', socket_type='NodeSocketBool', parent = geometry_panel)
    mirrow_socket.default_value = False
    mirrow_socket.attribute_domain = 'POINT'
    mirrow_socket.default_input = 'VALUE'
    mirrow_socket.structure_type = 'AUTO'

    # Socket LineLenth
    linelenth_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="LineLenth", in_out='INPUT', socket_type='NodeSocketFloat', parent = geometry_panel)
    linelenth_socket.default_value = -30.0
    linelenth_socket.min_value = -10000.0
    linelenth_socket.max_value = 10000.0
    linelenth_socket.subtype = 'NONE'
    linelenth_socket.attribute_domain = 'POINT'
    linelenth_socket.default_input = 'VALUE'
    linelenth_socket.structure_type = 'AUTO'

    # Socket LineTop
    linetop_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="LineTop", in_out='INPUT', socket_type='NodeSocketFloat', parent = geometry_panel)
    linetop_socket.default_value = 0.0
    linetop_socket.min_value = 0.0
    linetop_socket.max_value = 10000.0
    linetop_socket.subtype = 'NONE'
    linetop_socket.attribute_domain = 'POINT'
    linetop_socket.default_input = 'VALUE'
    linetop_socket.structure_type = 'AUTO'

    # Socket LineBottom
    linebottom_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="LineBottom", in_out='INPUT', socket_type='NodeSocketFloat', parent = geometry_panel)
    linebottom_socket.default_value = 1.0
    linebottom_socket.min_value = 0.0
    linebottom_socket.max_value = 10000.0
    linebottom_socket.subtype = 'NONE'
    linebottom_socket.attribute_domain = 'POINT'
    linebottom_socket.default_input = 'VALUE'
    linebottom_socket.structure_type = 'AUTO'


    # Panel Render
    render_panel = ugrs_mainnodetree_v1_0_1.interface.new_panel("Render")
    # Socket ShaderMode
    shadermode_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="ShaderMode", in_out='INPUT', socket_type='NodeSocketMenu', parent = render_panel)
    shadermode_socket.attribute_domain = 'POINT'
    shadermode_socket.default_input = 'VALUE'
    shadermode_socket.menu_expanded = True
    shadermode_socket.structure_type = 'AUTO'

    # Socket Precompute
    precompute_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Precompute", in_out='INPUT', socket_type='NodeSocketBool', parent = render_panel)
    precompute_socket.default_value = True
    precompute_socket.attribute_domain = 'POINT'
    precompute_socket.default_input = 'VALUE'
    precompute_socket.structure_type = 'AUTO'

    # Socket OutputChannle
    outputchannle_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="OutputChannle", in_out='INPUT', socket_type='NodeSocketMenu', parent = render_panel)
    outputchannle_socket.attribute_domain = 'POINT'
    outputchannle_socket.default_input = 'VALUE'
    outputchannle_socket.menu_expanded = True
    outputchannle_socket.structure_type = 'AUTO'

    # Socket SH_start
    sh_start_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="SH_start", in_out='INPUT', socket_type='NodeSocketInt', parent = render_panel)
    sh_start_socket.default_value = 0
    sh_start_socket.min_value = 0
    sh_start_socket.max_value = 3
    sh_start_socket.subtype = 'NONE'
    sh_start_socket.attribute_domain = 'POINT'
    sh_start_socket.default_input = 'VALUE'
    sh_start_socket.structure_type = 'AUTO'

    # Socket SH_end
    sh_end_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="SH_end", in_out='INPUT', socket_type='NodeSocketInt', parent = render_panel)
    sh_end_socket.default_value = 3
    sh_end_socket.min_value = 0
    sh_end_socket.max_value = 3
    sh_end_socket.subtype = 'NONE'
    sh_end_socket.attribute_domain = 'POINT'
    sh_end_socket.default_input = 'VALUE'
    sh_end_socket.structure_type = 'AUTO'

    # Socket Mode
    mode_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Mode", in_out='INPUT', socket_type='NodeSocketMenu', parent = render_panel)
    mode_socket.attribute_domain = 'POINT'
    mode_socket.default_input = 'VALUE'
    mode_socket.menu_expanded = True
    mode_socket.structure_type = 'AUTO'
    mode_socket.optional_label = True

    # Socket Length
    length_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Length", in_out='INPUT', socket_type='NodeSocketBool', parent = render_panel)
    length_socket.default_value = False
    length_socket.attribute_domain = 'POINT'
    length_socket.default_input = 'VALUE'
    length_socket.structure_type = 'AUTO'

    # Socket Normalize
    normalize_socket = ugrs_mainnodetree_v1_0_1.interface.new_socket(name="Normalize", in_out='INPUT', socket_type='NodeSocketBool', parent = render_panel)
    normalize_socket.default_value = False
    normalize_socket.attribute_domain = 'POINT'
    normalize_socket.default_input = 'VALUE'
    normalize_socket.structure_type = 'AUTO'


    # Initialize ugrs_mainnodetree_v1_0_1 nodes

    # Node Collection Info
    collection_info = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeCollectionInfo")
    collection_info.name = "Collection Info"
    collection_info.transform_space = 'ORIGINAL'
    # Separate Children
    collection_info.inputs[1].default_value = True
    # Reset Children
    collection_info.inputs[2].default_value = False

    # Node Index
    index = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputIndex")
    index.name = "Index"

    # Node Compare
    compare = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeCompare")
    compare.name = "Compare"
    compare.data_type = 'INT'
    compare.mode = 'ELEMENT'
    compare.operation = 'NOT_EQUAL'

    # Node Delete Geometry
    delete_geometry = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry.name = "Delete Geometry"
    delete_geometry.domain = 'INSTANCE'
    delete_geometry.mode = 'ALL'

    # Node Group Input
    group_input = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"
    group_input.outputs[0].hide = True
    group_input.outputs[1].hide = True
    group_input.outputs[2].hide = True
    group_input.outputs[3].hide = True
    group_input.outputs[4].hide = True
    group_input.outputs[5].hide = True
    group_input.outputs[6].hide = True
    group_input.outputs[7].hide = True
    group_input.outputs[8].hide = True
    group_input.outputs[9].hide = True
    group_input.outputs[10].hide = True
    group_input.outputs[11].hide = True
    group_input.outputs[12].hide = True
    group_input.outputs[13].hide = True
    group_input.outputs[15].hide = True
    group_input.outputs[16].hide = True
    group_input.outputs[20].hide = True
    group_input.outputs[21].hide = True
    group_input.outputs[22].hide = True
    group_input.outputs[23].hide = True
    group_input.outputs[24].hide = True
    group_input.outputs[25].hide = True
    group_input.outputs[26].hide = True
    group_input.outputs[27].hide = True
    group_input.outputs[28].hide = True
    group_input.outputs[29].hide = True
    group_input.outputs[30].hide = True
    group_input.outputs[31].hide = True
    group_input.outputs[32].hide = True
    group_input.outputs[33].hide = True
    group_input.outputs[34].hide = True
    group_input.outputs[35].hide = True
    group_input.outputs[36].hide = True
    group_input.outputs[37].hide = True
    group_input.outputs[38].hide = True
    group_input.outputs[39].hide = True
    group_input.outputs[40].hide = True

    # Node Simulation Input
    simulation_input = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSimulationInput")
    simulation_input.name = "Simulation Input"
    # Node Simulation Output
    simulation_output = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSimulationOutput")
    simulation_output.name = "Simulation Output"
    simulation_output.active_index = 0
    simulation_output.state_items.clear()
    # Create item "Current Frame"
    simulation_output.state_items.new('FLOAT', "Current Frame")
    simulation_output.state_items[0].attribute_domain = 'POINT'
    # Skip
    simulation_output.inputs[0].default_value = False

    # Node Math_Add
    math_add = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    math_add.name = "Math_Add"
    math_add.hide = True
    math_add.operation = 'ADD'
    math_add.use_clamp = False

    # Node Math_Multiply
    math_multiply = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    math_multiply.name = "Math_Multiply"
    math_multiply.hide = True
    math_multiply.operation = 'MULTIPLY'
    math_multiply.use_clamp = False
    # Value
    math_multiply.inputs[0].default_value = 0.5

    # Node Math_Multiply.001
    math_multiply_001 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    math_multiply_001.name = "Math_Multiply.001"
    math_multiply_001.hide = True
    math_multiply_001.operation = 'MULTIPLY'
    math_multiply_001.use_clamp = False

    # Node 组输入.001
    ____001 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____001.name = "组输入.001"
    ____001.outputs[0].hide = True
    ____001.outputs[1].hide = True
    ____001.outputs[2].hide = True
    ____001.outputs[3].hide = True
    ____001.outputs[4].hide = True
    ____001.outputs[6].hide = True
    ____001.outputs[7].hide = True
    ____001.outputs[8].hide = True
    ____001.outputs[9].hide = True
    ____001.outputs[10].hide = True
    ____001.outputs[11].hide = True
    ____001.outputs[12].hide = True
    ____001.outputs[13].hide = True
    ____001.outputs[14].hide = True
    ____001.outputs[15].hide = True
    ____001.outputs[16].hide = True
    ____001.outputs[17].hide = True
    ____001.outputs[18].hide = True
    ____001.outputs[19].hide = True
    ____001.outputs[20].hide = True
    ____001.outputs[21].hide = True
    ____001.outputs[22].hide = True
    ____001.outputs[23].hide = True
    ____001.outputs[24].hide = True
    ____001.outputs[25].hide = True
    ____001.outputs[26].hide = True
    ____001.outputs[27].hide = True
    ____001.outputs[28].hide = True
    ____001.outputs[29].hide = True
    ____001.outputs[30].hide = True
    ____001.outputs[31].hide = True
    ____001.outputs[32].hide = True
    ____001.outputs[33].hide = True
    ____001.outputs[34].hide = True
    ____001.outputs[35].hide = True
    ____001.outputs[36].hide = True
    ____001.outputs[37].hide = True
    ____001.outputs[38].hide = True
    ____001.outputs[39].hide = True
    ____001.outputs[40].hide = True

    # Node 组输入.003
    ____003 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____003.name = "组输入.003"
    ____003.outputs[0].hide = True
    ____003.outputs[1].hide = True
    ____003.outputs[2].hide = True
    ____003.outputs[3].hide = True
    ____003.outputs[4].hide = True
    ____003.outputs[5].hide = True
    ____003.outputs[6].hide = True
    ____003.outputs[7].hide = True
    ____003.outputs[8].hide = True
    ____003.outputs[9].hide = True
    ____003.outputs[10].hide = True
    ____003.outputs[11].hide = True
    ____003.outputs[12].hide = True
    ____003.outputs[13].hide = True
    ____003.outputs[14].hide = True
    ____003.outputs[15].hide = True
    ____003.outputs[16].hide = True
    ____003.outputs[17].hide = True
    ____003.outputs[18].hide = True
    ____003.outputs[19].hide = True
    ____003.outputs[20].hide = True
    ____003.outputs[21].hide = True
    ____003.outputs[22].hide = True
    ____003.outputs[23].hide = True
    ____003.outputs[24].hide = True
    ____003.outputs[25].hide = True
    ____003.outputs[26].hide = True
    ____003.outputs[27].hide = True
    ____003.outputs[28].hide = True
    ____003.outputs[29].hide = True
    ____003.outputs[30].hide = True
    ____003.outputs[31].hide = True
    ____003.outputs[32].hide = True
    ____003.outputs[33].hide = True
    ____003.outputs[34].hide = True
    ____003.outputs[35].hide = True
    ____003.outputs[36].hide = True
    ____003.outputs[37].hide = True
    ____003.outputs[38].hide = True
    ____003.outputs[39].hide = True
    ____003.outputs[40].hide = True

    # Node 帧
    _ = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    _.label = "FrameIndex"
    _.name = "帧"
    _.label_size = 20
    _.shrink = True

    # Node 群组
    __ = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    __.name = "群组"
    __.node_tree = bpy.data.node_groups[node_tree_names[menu_switching_1_node_group]]

    # Node 合并 XYZ.002
    ___xyz_002 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_002.name = "合并 XYZ.002"

    # Node 已命名属性.012
    ______012 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______012.name = "已命名属性.012"
    ______012.data_type = 'FLOAT'
    # Name
    ______012.inputs[0].default_value = "scale_1"

    # Node 已命名属性.013
    ______013 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______013.name = "已命名属性.013"
    ______013.data_type = 'FLOAT'
    # Name
    ______013.inputs[0].default_value = "scale_2"

    # Node 已命名属性.014
    ______014 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______014.name = "已命名属性.014"
    ______014.data_type = 'FLOAT'
    # Name
    ______014.inputs[0].default_value = "scale_0"

    # Node 已命名属性.015
    ______015 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______015.name = "已命名属性.015"
    ______015.data_type = 'FLOAT'
    # Name
    ______015.inputs[0].default_value = "rot_0"

    # Node 已命名属性.016
    ______016 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______016.name = "已命名属性.016"
    ______016.data_type = 'FLOAT'
    # Name
    ______016.inputs[0].default_value = "rot_1"

    # Node 已命名属性.017
    ______017 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______017.name = "已命名属性.017"
    ______017.data_type = 'FLOAT'
    # Name
    ______017.inputs[0].default_value = "rot_2"

    # Node 已命名属性.018
    ______018 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______018.name = "已命名属性.018"
    ______018.data_type = 'FLOAT'
    # Name
    ______018.inputs[0].default_value = "rot_3"

    # Node 运算.008
    ___008 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___008.name = "运算.008"
    ___008.hide = True
    ___008.operation = 'MULTIPLY'
    ___008.use_clamp = False

    # Node 运算.009
    ___009 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___009.name = "运算.009"
    ___009.hide = True
    ___009.operation = 'MULTIPLY'
    ___009.use_clamp = False

    # Node 立方体.001
    ____001_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMeshCube")
    ____001_1.name = "立方体.001"
    ____001_1.hide = True
    # Size
    ____001_1.inputs[0].default_value = (2.0, 2.0, 2.0)
    # Vertices X
    ____001_1.inputs[1].default_value = 2
    # Vertices Y
    ____001_1.inputs[2].default_value = 2
    # Vertices Z
    ____001_1.inputs[3].default_value = 2

    # Node 设置位置.001
    _____001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSetPosition")
    _____001.name = "设置位置.001"
    # Selection
    _____001.inputs[1].default_value = True
    # Position
    _____001.inputs[2].default_value = (0.0, 0.0, 0.0)

    # Node 已命名属性.019
    ______019 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______019.name = "已命名属性.019"
    ______019.data_type = 'FLOAT'
    # Name
    ______019.inputs[0].default_value = "motion_0"

    # Node 已命名属性.020
    ______020 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______020.name = "已命名属性.020"
    ______020.data_type = 'FLOAT'
    # Name
    ______020.inputs[0].default_value = "motion_1"

    # Node 已命名属性.021
    ______021 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______021.name = "已命名属性.021"
    ______021.data_type = 'FLOAT'
    # Name
    ______021.inputs[0].default_value = "motion_2"

    # Node 合并 XYZ.003
    ___xyz_003 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_003.name = "合并 XYZ.003"

    # Node 已命名属性.022
    ______022 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______022.name = "已命名属性.022"
    ______022.data_type = 'FLOAT'
    # Name
    ______022.inputs[0].default_value = "t_scale"

    # Node 矢量运算.010
    _____010 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____010.name = "矢量运算.010"
    _____010.operation = 'SCALE'

    # Node 运算.012
    ___012 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___012.name = "运算.012"
    ___012.hide = True
    ___012.operation = 'SUBTRACT'
    ___012.use_clamp = False

    # Node 已命名属性.023
    ______023 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______023.name = "已命名属性.023"
    ______023.data_type = 'FLOAT'
    # Name
    ______023.inputs[0].default_value = "ttt"

    # Node 运算.013
    ___013 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___013.name = "运算.013"
    ___013.operation = 'EXPONENT'
    ___013.use_clamp = False

    # Node 运算.014
    ___014 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___014.name = "运算.014"
    ___014.hide = True
    ___014.operation = 'SUBTRACT'
    ___014.use_clamp = False

    # Node 运算.015
    ___015 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___015.name = "运算.015"
    ___015.operation = 'POWER'
    ___015.use_clamp = False
    # Value_001
    ___015.inputs[1].default_value = 2.0

    # Node 运算.016
    ___016 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___016.name = "运算.016"
    ___016.operation = 'MULTIPLY'
    ___016.use_clamp = False
    # Value_001
    ___016.inputs[1].default_value = -0.5

    # Node 运算.017
    ___017 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___017.name = "运算.017"
    ___017.operation = 'DIVIDE'
    ___017.use_clamp = False

    # Node 运算.018
    ___018 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___018.name = "运算.018"
    ___018.operation = 'EXPONENT'
    ___018.use_clamp = False

    # Node 已命名属性.024
    ______024 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______024.name = "已命名属性.024"
    ______024.data_type = 'FLOAT'
    # Name
    ______024.inputs[0].default_value = "ttt"

    # Node 运算.020
    ___020 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___020.name = "运算.020"
    ___020.operation = 'POWER'
    ___020.use_clamp = False
    # Value_001
    ___020.inputs[1].default_value = 0.3333333432674408

    # Node 实例化于点上.003
    _______003 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInstanceOnPoints")
    _______003.name = "实例化于点上.003"
    # Selection
    _______003.inputs[1].default_value = True
    # Pick Instance
    _______003.inputs[3].default_value = False
    # Instance Index
    _______003.inputs[4].default_value = 0

    # Node 轴向 转换为 旋转.002
    __________002 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeAxesToRotation")
    __________002.name = "轴向 转换为 旋转.002"
    __________002.primary_axis = 'Z'
    __________002.secondary_axis = 'X'
    # Secondary Axis
    __________002.inputs[1].default_value = (1.0, 0.0, 0.0)

    # Node 锥形.001
    ___001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMeshCone")
    ___001.name = "锥形.001"
    ___001.fill_type = 'NGON'
    # Vertices
    ___001.inputs[0].default_value = 3
    # Side Segments
    ___001.inputs[1].default_value = 1
    # Fill Segments
    ___001.inputs[2].default_value = 1

    # Node 矢量运算.012
    _____012 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____012.name = "矢量运算.012"
    _____012.operation = 'LENGTH'

    # Node 运算.021
    ___021 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___021.name = "运算.021"
    ___021.operation = 'MULTIPLY'
    ___021.use_clamp = False
    # Value_001
    ___021.inputs[1].default_value = 0.0010000000474974513

    # Node 运算.022
    ___022 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___022.name = "运算.022"
    ___022.operation = 'MULTIPLY'
    ___022.use_clamp = False
    # Value_001
    ___022.inputs[1].default_value = 0.0010000000474974513

    # Node 合并 XYZ.004
    ___xyz_004 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_004.name = "合并 XYZ.004"
    ___xyz_004.hide = True

    # Node 已命名属性.025
    ______025 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______025.name = "已命名属性.025"
    ______025.data_type = 'FLOAT'
    # Name
    ______025.inputs[0].default_value = "motion_0"

    # Node 已命名属性.026
    ______026 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______026.name = "已命名属性.026"
    ______026.data_type = 'FLOAT'
    # Name
    ______026.inputs[0].default_value = "motion_1"

    # Node 已命名属性.027
    ______027 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______027.name = "已命名属性.027"
    ______027.data_type = 'FLOAT'
    # Name
    ______027.inputs[0].default_value = "motion_2"

    # Node 菜单切换
    ____ = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    ____.name = "菜单切换"
    ____.active_index = 1
    ____.data_type = 'GEOMETRY'
    ____.enum_items.clear()
    ____.enum_items.new("PointCloud")
    ____.enum_items[0].description = ""
    ____.enum_items.new("Mesh")
    ____.enum_items[1].description = ""
    ____.enum_items.new("MotionLine")
    ____.enum_items[2].description = ""

    # Node 转接点.001
    ____001_2 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____001_2.name = "转接点.001"
    ____001_2.hide = True
    ____001_2.socket_idname = "NodeSocketFloat"
    # Node 帧.001
    __001 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    __001.label = "Compute_marginal_t"
    __001.name = "帧.001"
    __001.label_size = 20
    __001.shrink = True

    # Node 转接点.004
    ____004 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____004.name = "转接点.004"
    ____004.hide = True
    ____004.socket_idname = "NodeSocketFloat"
    # Node 群组.002
    ___002 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___002.name = "群组.002"
    ___002.node_tree = bpy.data.node_groups[node_tree_names[input_method_1_node_group]]

    # Node 组输入.006
    ____006 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____006.name = "组输入.006"
    ____006.outputs[0].hide = True
    ____006.outputs[1].hide = True
    ____006.outputs[2].hide = True
    ____006.outputs[3].hide = True
    ____006.outputs[5].hide = True
    ____006.outputs[6].hide = True
    ____006.outputs[7].hide = True
    ____006.outputs[8].hide = True
    ____006.outputs[9].hide = True
    ____006.outputs[10].hide = True
    ____006.outputs[11].hide = True
    ____006.outputs[12].hide = True
    ____006.outputs[13].hide = True
    ____006.outputs[14].hide = True
    ____006.outputs[15].hide = True
    ____006.outputs[16].hide = True
    ____006.outputs[17].hide = True
    ____006.outputs[18].hide = True
    ____006.outputs[19].hide = True
    ____006.outputs[20].hide = True
    ____006.outputs[21].hide = True
    ____006.outputs[22].hide = True
    ____006.outputs[23].hide = True
    ____006.outputs[24].hide = True
    ____006.outputs[25].hide = True
    ____006.outputs[26].hide = True
    ____006.outputs[27].hide = True
    ____006.outputs[28].hide = True
    ____006.outputs[29].hide = True
    ____006.outputs[30].hide = True
    ____006.outputs[31].hide = True
    ____006.outputs[32].hide = True
    ____006.outputs[33].hide = True
    ____006.outputs[34].hide = True
    ____006.outputs[35].hide = True
    ____006.outputs[36].hide = True
    ____006.outputs[37].hide = True
    ____006.outputs[38].hide = True
    ____006.outputs[39].hide = True
    ____006.outputs[40].hide = True

    # Node 组输入.008
    ____008 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____008.name = "组输入.008"
    ____008.outputs[0].hide = True
    ____008.outputs[1].hide = True
    ____008.outputs[2].hide = True
    ____008.outputs[3].hide = True
    ____008.outputs[4].hide = True
    ____008.outputs[5].hide = True
    ____008.outputs[7].hide = True
    ____008.outputs[8].hide = True
    ____008.outputs[9].hide = True
    ____008.outputs[10].hide = True
    ____008.outputs[11].hide = True
    ____008.outputs[12].hide = True
    ____008.outputs[13].hide = True
    ____008.outputs[14].hide = True
    ____008.outputs[15].hide = True
    ____008.outputs[16].hide = True
    ____008.outputs[17].hide = True
    ____008.outputs[18].hide = True
    ____008.outputs[19].hide = True
    ____008.outputs[20].hide = True
    ____008.outputs[21].hide = True
    ____008.outputs[22].hide = True
    ____008.outputs[23].hide = True
    ____008.outputs[24].hide = True
    ____008.outputs[25].hide = True
    ____008.outputs[26].hide = True
    ____008.outputs[27].hide = True
    ____008.outputs[28].hide = True
    ____008.outputs[29].hide = True
    ____008.outputs[30].hide = True
    ____008.outputs[31].hide = True
    ____008.outputs[32].hide = True
    ____008.outputs[33].hide = True
    ____008.outputs[34].hide = True
    ____008.outputs[35].hide = True
    ____008.outputs[36].hide = True
    ____008.outputs[37].hide = True
    ____008.outputs[38].hide = True
    ____008.outputs[39].hide = True
    ____008.outputs[40].hide = True

    # Node 物体信息.001
    _____001_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____001_1.name = "物体信息.001"
    _____001_1.transform_space = 'ORIGINAL'
    # As Instance
    _____001_1.inputs[1].default_value = False

    # Node input_point_radius.001
    input_point_radius_001 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_001.name = "input_point_radius.001"
    input_point_radius_001.outputs[0].hide = True
    input_point_radius_001.outputs[1].hide = True
    input_point_radius_001.outputs[2].hide = True
    input_point_radius_001.outputs[3].hide = True
    input_point_radius_001.outputs[4].hide = True
    input_point_radius_001.outputs[5].hide = True
    input_point_radius_001.outputs[6].hide = True
    input_point_radius_001.outputs[7].hide = True
    input_point_radius_001.outputs[8].hide = True
    input_point_radius_001.outputs[9].hide = True
    input_point_radius_001.outputs[11].hide = True
    input_point_radius_001.outputs[12].hide = True
    input_point_radius_001.outputs[13].hide = True
    input_point_radius_001.outputs[14].hide = True
    input_point_radius_001.outputs[15].hide = True
    input_point_radius_001.outputs[16].hide = True
    input_point_radius_001.outputs[17].hide = True
    input_point_radius_001.outputs[18].hide = True
    input_point_radius_001.outputs[19].hide = True
    input_point_radius_001.outputs[20].hide = True
    input_point_radius_001.outputs[21].hide = True
    input_point_radius_001.outputs[22].hide = True
    input_point_radius_001.outputs[23].hide = True
    input_point_radius_001.outputs[24].hide = True
    input_point_radius_001.outputs[25].hide = True
    input_point_radius_001.outputs[26].hide = True
    input_point_radius_001.outputs[27].hide = True
    input_point_radius_001.outputs[28].hide = True
    input_point_radius_001.outputs[29].hide = True
    input_point_radius_001.outputs[30].hide = True
    input_point_radius_001.outputs[31].hide = True
    input_point_radius_001.outputs[32].hide = True
    input_point_radius_001.outputs[33].hide = True
    input_point_radius_001.outputs[34].hide = True
    input_point_radius_001.outputs[35].hide = True
    input_point_radius_001.outputs[36].hide = True
    input_point_radius_001.outputs[37].hide = True
    input_point_radius_001.outputs[38].hide = True
    input_point_radius_001.outputs[39].hide = True
    input_point_radius_001.outputs[40].hide = True

    # Node 转接点.006
    ____006_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____006_1.name = "转接点.006"
    ____006_1.socket_idname = "NodeSocketBool"
    # Node input_point_radius.003
    input_point_radius_003 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_003.name = "input_point_radius.003"
    input_point_radius_003.outputs[0].hide = True
    input_point_radius_003.outputs[1].hide = True
    input_point_radius_003.outputs[2].hide = True
    input_point_radius_003.outputs[3].hide = True
    input_point_radius_003.outputs[4].hide = True
    input_point_radius_003.outputs[5].hide = True
    input_point_radius_003.outputs[6].hide = True
    input_point_radius_003.outputs[7].hide = True
    input_point_radius_003.outputs[8].hide = True
    input_point_radius_003.outputs[9].hide = True
    input_point_radius_003.outputs[10].hide = True
    input_point_radius_003.outputs[11].hide = True
    input_point_radius_003.outputs[12].hide = True
    input_point_radius_003.outputs[13].hide = True
    input_point_radius_003.outputs[14].hide = True
    input_point_radius_003.outputs[15].hide = True
    input_point_radius_003.outputs[16].hide = True
    input_point_radius_003.outputs[17].hide = True
    input_point_radius_003.outputs[18].hide = True
    input_point_radius_003.outputs[19].hide = True
    input_point_radius_003.outputs[20].hide = True
    input_point_radius_003.outputs[22].hide = True
    input_point_radius_003.outputs[23].hide = True
    input_point_radius_003.outputs[24].hide = True
    input_point_radius_003.outputs[25].hide = True
    input_point_radius_003.outputs[26].hide = True
    input_point_radius_003.outputs[27].hide = True
    input_point_radius_003.outputs[28].hide = True
    input_point_radius_003.outputs[29].hide = True
    input_point_radius_003.outputs[30].hide = True
    input_point_radius_003.outputs[31].hide = True
    input_point_radius_003.outputs[32].hide = True
    input_point_radius_003.outputs[33].hide = True
    input_point_radius_003.outputs[34].hide = True
    input_point_radius_003.outputs[35].hide = True
    input_point_radius_003.outputs[36].hide = True
    input_point_radius_003.outputs[37].hide = True
    input_point_radius_003.outputs[38].hide = True
    input_point_radius_003.outputs[39].hide = True
    input_point_radius_003.outputs[40].hide = True

    # Node 切换.001
    ___001_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___001_1.name = "切换.001"
    ___001_1.input_type = 'GEOMETRY'

    # Node input_point_radius.005
    input_point_radius_005 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_005.name = "input_point_radius.005"
    input_point_radius_005.outputs[0].hide = True
    input_point_radius_005.outputs[1].hide = True
    input_point_radius_005.outputs[2].hide = True
    input_point_radius_005.outputs[3].hide = True
    input_point_radius_005.outputs[4].hide = True
    input_point_radius_005.outputs[5].hide = True
    input_point_radius_005.outputs[6].hide = True
    input_point_radius_005.outputs[7].hide = True
    input_point_radius_005.outputs[8].hide = True
    input_point_radius_005.outputs[9].hide = True
    input_point_radius_005.outputs[10].hide = True
    input_point_radius_005.outputs[11].hide = True
    input_point_radius_005.outputs[12].hide = True
    input_point_radius_005.outputs[13].hide = True
    input_point_radius_005.outputs[14].hide = True
    input_point_radius_005.outputs[15].hide = True
    input_point_radius_005.outputs[16].hide = True
    input_point_radius_005.outputs[17].hide = True
    input_point_radius_005.outputs[18].hide = True
    input_point_radius_005.outputs[19].hide = True
    input_point_radius_005.outputs[20].hide = True
    input_point_radius_005.outputs[21].hide = True
    input_point_radius_005.outputs[22].hide = True
    input_point_radius_005.outputs[23].hide = True
    input_point_radius_005.outputs[24].hide = True
    input_point_radius_005.outputs[25].hide = True
    input_point_radius_005.outputs[26].hide = True
    input_point_radius_005.outputs[27].hide = True
    input_point_radius_005.outputs[28].hide = True
    input_point_radius_005.outputs[32].hide = True
    input_point_radius_005.outputs[33].hide = True
    input_point_radius_005.outputs[34].hide = True
    input_point_radius_005.outputs[35].hide = True
    input_point_radius_005.outputs[36].hide = True
    input_point_radius_005.outputs[37].hide = True
    input_point_radius_005.outputs[38].hide = True
    input_point_radius_005.outputs[39].hide = True
    input_point_radius_005.outputs[40].hide = True

    # Node 运算.027
    ___027 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___027.name = "运算.027"
    ___027.operation = 'MULTIPLY'
    ___027.use_clamp = False
    # Value_001
    ___027.inputs[1].default_value = 0.0010000000474974513

    # Node 组输入.009
    ____009 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____009.name = "组输入.009"
    ____009.outputs[0].hide = True
    ____009.outputs[1].hide = True
    ____009.outputs[2].hide = True
    ____009.outputs[3].hide = True
    ____009.outputs[4].hide = True
    ____009.outputs[5].hide = True
    ____009.outputs[6].hide = True
    ____009.outputs[7].hide = True
    ____009.outputs[8].hide = True
    ____009.outputs[10].hide = True
    ____009.outputs[11].hide = True
    ____009.outputs[12].hide = True
    ____009.outputs[13].hide = True
    ____009.outputs[14].hide = True
    ____009.outputs[15].hide = True
    ____009.outputs[16].hide = True
    ____009.outputs[17].hide = True
    ____009.outputs[18].hide = True
    ____009.outputs[19].hide = True
    ____009.outputs[20].hide = True
    ____009.outputs[21].hide = True
    ____009.outputs[22].hide = True
    ____009.outputs[23].hide = True
    ____009.outputs[24].hide = True
    ____009.outputs[25].hide = True
    ____009.outputs[26].hide = True
    ____009.outputs[27].hide = True
    ____009.outputs[28].hide = True
    ____009.outputs[29].hide = True
    ____009.outputs[30].hide = True
    ____009.outputs[31].hide = True
    ____009.outputs[32].hide = True
    ____009.outputs[33].hide = True
    ____009.outputs[34].hide = True
    ____009.outputs[35].hide = True
    ____009.outputs[36].hide = True
    ____009.outputs[37].hide = True
    ____009.outputs[38].hide = True
    ____009.outputs[39].hide = True
    ____009.outputs[40].hide = True

    # Node 转接点.007
    ____007 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____007.name = "转接点.007"
    ____007.socket_idname = "NodeSocketFloat"
    # Node 转接点.008
    ____008_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____008_1.name = "转接点.008"
    ____008_1.hide = True
    ____008_1.socket_idname = "NodeSocketFloat"
    # Node 运算.029
    ___029 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___029.name = "运算.029"
    ___029.hide = True
    ___029.operation = 'DIVIDE'
    ___029.use_clamp = False

    # Node 帧.003
    __003 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    __003.name = "帧.003"
    __003.hide = True
    __003.label_size = 20
    __003.shrink = True

    # Node 帧.004
    __004 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    __004.name = "帧.004"
    __004.label_size = 20
    __004.shrink = True

    # Node 帧.006
    __006 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    __006.name = "帧.006"
    __006.label_size = 20
    __006.shrink = True

    # Node 转接点.009
    ____009_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____009_1.name = "转接点.009"
    ____009_1.socket_idname = "NodeSocketFloat"
    # Node 帧.008
    __008 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    __008.label = "input"
    __008.name = "帧.008"
    __008.label_size = 20
    __008.shrink = True

    # Node 菜单切换.001
    _____001_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____001_2.name = "菜单切换.001"
    _____001_2.active_index = 5
    _____001_2.data_type = 'VECTOR'
    _____001_2.enum_items.clear()
    _____001_2.enum_items.new("Final color")
    _____001_2.enum_items[0].description = ""
    _____001_2.enum_items.new("optical flows")
    _____001_2.enum_items[1].description = ""
    _____001_2.enum_items.new("Normal")
    _____001_2.enum_items[2].description = ""
    _____001_2.enum_items.new("depth")
    _____001_2.enum_items[3].description = ""
    _____001_2.enum_items.new("Albedo")
    _____001_2.enum_items[4].description = ""
    _____001_2.enum_items.new("Alphac hannel")
    _____001_2.enum_items[5].description = ""
    _____001_2.enum_items.new("Derict")
    _____001_2.enum_items[6].description = ""
    _____001_2.enum_items.new("t_scale")
    _____001_2.enum_items[7].description = ""

    # Node 矢量运算.013
    _____013 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____013.name = "矢量运算.013"
    _____013.operation = 'SCALE'

    # Node input_point_radius.007
    input_point_radius_007 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_007.name = "input_point_radius.007"
    input_point_radius_007.outputs[0].hide = True
    input_point_radius_007.outputs[1].hide = True
    input_point_radius_007.outputs[2].hide = True
    input_point_radius_007.outputs[3].hide = True
    input_point_radius_007.outputs[4].hide = True
    input_point_radius_007.outputs[5].hide = True
    input_point_radius_007.outputs[6].hide = True
    input_point_radius_007.outputs[7].hide = True
    input_point_radius_007.outputs[8].hide = True
    input_point_radius_007.outputs[9].hide = True
    input_point_radius_007.outputs[10].hide = True
    input_point_radius_007.outputs[11].hide = True
    input_point_radius_007.outputs[12].hide = True
    input_point_radius_007.outputs[13].hide = True
    input_point_radius_007.outputs[14].hide = True
    input_point_radius_007.outputs[15].hide = True
    input_point_radius_007.outputs[16].hide = True
    input_point_radius_007.outputs[17].hide = True
    input_point_radius_007.outputs[18].hide = True
    input_point_radius_007.outputs[19].hide = True
    input_point_radius_007.outputs[20].hide = True
    input_point_radius_007.outputs[21].hide = True
    input_point_radius_007.outputs[22].hide = True
    input_point_radius_007.outputs[23].hide = True
    input_point_radius_007.outputs[24].hide = True
    input_point_radius_007.outputs[25].hide = True
    input_point_radius_007.outputs[26].hide = True
    input_point_radius_007.outputs[27].hide = True
    input_point_radius_007.outputs[29].hide = True
    input_point_radius_007.outputs[30].hide = True
    input_point_radius_007.outputs[31].hide = True
    input_point_radius_007.outputs[32].hide = True
    input_point_radius_007.outputs[33].hide = True
    input_point_radius_007.outputs[34].hide = True
    input_point_radius_007.outputs[35].hide = True
    input_point_radius_007.outputs[36].hide = True
    input_point_radius_007.outputs[37].hide = True
    input_point_radius_007.outputs[38].hide = True
    input_point_radius_007.outputs[39].hide = True
    input_point_radius_007.outputs[40].hide = True

    # Node 切换.002
    ___002_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___002_1.name = "切换.002"
    ___002_1.input_type = 'GEOMETRY'

    # Node 合并几何.002
    _____002 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeJoinGeometry")
    _____002.name = "合并几何.002"

    # Node 变换几何体
    _____ = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeTransform")
    _____.name = "变换几何体"
    # Mode
    _____.inputs[1].default_value = 'Components'
    # Translation
    _____.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Rotation
    _____.inputs[3].default_value = (3.1415927410125732, 0.0, 0.0)
    # Scale
    _____.inputs[4].default_value = (1.0, 1.0, 1.0)

    # Node 帧.010
    __010 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeFrame")
    __010.label = "sigmod"
    __010.name = "帧.010"
    __010.label_size = 20
    __010.shrink = True

    # Node 已命名属性.004
    ______004 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______004.name = "已命名属性.004"
    ______004.data_type = 'FLOAT'
    # Name
    ______004.inputs[0].default_value = "opacity"

    # Node 运算.039
    ___039 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___039.name = "运算.039"
    ___039.hide = True
    ___039.operation = 'MULTIPLY'
    ___039.use_clamp = False
    ___039.inputs[2].hide = True

    # Node input_point_radius.008
    input_point_radius_008 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_008.name = "input_point_radius.008"
    input_point_radius_008.outputs[0].hide = True
    input_point_radius_008.outputs[1].hide = True
    input_point_radius_008.outputs[2].hide = True
    input_point_radius_008.outputs[3].hide = True
    input_point_radius_008.outputs[4].hide = True
    input_point_radius_008.outputs[5].hide = True
    input_point_radius_008.outputs[6].hide = True
    input_point_radius_008.outputs[7].hide = True
    input_point_radius_008.outputs[8].hide = True
    input_point_radius_008.outputs[9].hide = True
    input_point_radius_008.outputs[10].hide = True
    input_point_radius_008.outputs[11].hide = True
    input_point_radius_008.outputs[12].hide = True
    input_point_radius_008.outputs[13].hide = True
    input_point_radius_008.outputs[14].hide = True
    input_point_radius_008.outputs[15].hide = True
    input_point_radius_008.outputs[16].hide = True
    input_point_radius_008.outputs[17].hide = True
    input_point_radius_008.outputs[18].hide = True
    input_point_radius_008.outputs[19].hide = True
    input_point_radius_008.outputs[20].hide = True
    input_point_radius_008.outputs[21].hide = True
    input_point_radius_008.outputs[22].hide = True
    input_point_radius_008.outputs[23].hide = True
    input_point_radius_008.outputs[24].hide = True
    input_point_radius_008.outputs[26].hide = True
    input_point_radius_008.outputs[27].hide = True
    input_point_radius_008.outputs[28].hide = True
    input_point_radius_008.outputs[29].hide = True
    input_point_radius_008.outputs[30].hide = True
    input_point_radius_008.outputs[31].hide = True
    input_point_radius_008.outputs[32].hide = True
    input_point_radius_008.outputs[33].hide = True
    input_point_radius_008.outputs[34].hide = True
    input_point_radius_008.outputs[35].hide = True
    input_point_radius_008.outputs[36].hide = True
    input_point_radius_008.outputs[37].hide = True
    input_point_radius_008.outputs[38].hide = True
    input_point_radius_008.outputs[39].hide = True
    input_point_radius_008.outputs[40].hide = True

    # Node 菜单切换.002
    _____002_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____002_1.name = "菜单切换.002"
    _____002_1.active_index = 3
    _____002_1.data_type = 'FLOAT'
    _____002_1.enum_items.clear()
    _____002_1.enum_items.new("Opacity & Marginal")
    _____002_1.enum_items[0].description = ""
    _____002_1.enum_items.new("Only Marginal")
    _____002_1.enum_items[1].description = ""
    _____002_1.enum_items.new("Only Opacity")
    _____002_1.enum_items[2].description = ""
    _____002_1.enum_items.new("None")
    _____002_1.enum_items[3].description = ""
    # Item_3
    _____002_1.inputs[4].default_value = 1.0

    # Node 棱角球
    ___ = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMeshIcoSphere")
    ___.name = "棱角球"
    # Radius
    ___.inputs[0].default_value = 1.0
    # Subdivisions
    ___.inputs[1].default_value = 1

    # Node 组输入.011
    ____011 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____011.name = "组输入.011"
    ____011.outputs[0].hide = True
    ____011.outputs[1].hide = True
    ____011.outputs[2].hide = True
    ____011.outputs[3].hide = True
    ____011.outputs[4].hide = True
    ____011.outputs[5].hide = True
    ____011.outputs[6].hide = True
    ____011.outputs[8].hide = True
    ____011.outputs[9].hide = True
    ____011.outputs[10].hide = True
    ____011.outputs[11].hide = True
    ____011.outputs[12].hide = True
    ____011.outputs[13].hide = True
    ____011.outputs[14].hide = True
    ____011.outputs[15].hide = True
    ____011.outputs[16].hide = True
    ____011.outputs[17].hide = True
    ____011.outputs[18].hide = True
    ____011.outputs[19].hide = True
    ____011.outputs[20].hide = True
    ____011.outputs[21].hide = True
    ____011.outputs[22].hide = True
    ____011.outputs[23].hide = True
    ____011.outputs[24].hide = True
    ____011.outputs[25].hide = True
    ____011.outputs[26].hide = True
    ____011.outputs[27].hide = True
    ____011.outputs[28].hide = True
    ____011.outputs[29].hide = True
    ____011.outputs[30].hide = True
    ____011.outputs[31].hide = True
    ____011.outputs[32].hide = True
    ____011.outputs[33].hide = True
    ____011.outputs[34].hide = True
    ____011.outputs[35].hide = True
    ____011.outputs[36].hide = True
    ____011.outputs[37].hide = True
    ____011.outputs[38].hide = True
    ____011.outputs[39].hide = True
    ____011.outputs[40].hide = True

    # Node Collection Info.001
    collection_info_001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeCollectionInfo")
    collection_info_001.name = "Collection Info.001"
    collection_info_001.transform_space = 'ORIGINAL'
    # Separate Children
    collection_info_001.inputs[1].default_value = True
    # Reset Children
    collection_info_001.inputs[2].default_value = False

    # Node Index.001
    index_001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputIndex")
    index_001.name = "Index.001"

    # Node Compare.001
    compare_001 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeCompare")
    compare_001.name = "Compare.001"
    compare_001.hide = True
    compare_001.data_type = 'INT'
    compare_001.mode = 'ELEMENT'
    compare_001.operation = 'NOT_EQUAL'

    # Node Delete Geometry.001
    delete_geometry_001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDeleteGeometry")
    delete_geometry_001.name = "Delete Geometry.001"
    delete_geometry_001.domain = 'INSTANCE'
    delete_geometry_001.mode = 'ALL'

    # Node 运算.032
    ___032 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___032.name = "运算.032"
    ___032.operation = 'DIVIDE'
    ___032.use_clamp = False

    # Node 切换.003
    ___003 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___003.name = "切换.003"
    ___003.input_type = 'FLOAT'

    # Node 运算.033
    ___033 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___033.name = "运算.033"
    ___033.operation = 'WRAP'
    ___033.use_clamp = False
    ___033.inputs[2].hide = True
    # Value_002
    ___033.inputs[2].default_value = 0.0

    # Node 运算.040
    ___040 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___040.name = "运算.040"
    ___040.operation = 'FLOOR'
    ___040.use_clamp = False

    # Node 组输入.007
    ____007_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____007_1.name = "组输入.007"
    ____007_1.outputs[0].hide = True
    ____007_1.outputs[1].hide = True
    ____007_1.outputs[2].hide = True
    ____007_1.outputs[3].hide = True
    ____007_1.outputs[4].hide = True
    ____007_1.outputs[5].hide = True
    ____007_1.outputs[6].hide = True
    ____007_1.outputs[7].hide = True
    ____007_1.outputs[8].hide = True
    ____007_1.outputs[10].hide = True
    ____007_1.outputs[11].hide = True
    ____007_1.outputs[12].hide = True
    ____007_1.outputs[13].hide = True
    ____007_1.outputs[14].hide = True
    ____007_1.outputs[15].hide = True
    ____007_1.outputs[16].hide = True
    ____007_1.outputs[17].hide = True
    ____007_1.outputs[18].hide = True
    ____007_1.outputs[19].hide = True
    ____007_1.outputs[20].hide = True
    ____007_1.outputs[21].hide = True
    ____007_1.outputs[22].hide = True
    ____007_1.outputs[23].hide = True
    ____007_1.outputs[24].hide = True
    ____007_1.outputs[25].hide = True
    ____007_1.outputs[26].hide = True
    ____007_1.outputs[27].hide = True
    ____007_1.outputs[28].hide = True
    ____007_1.outputs[29].hide = True
    ____007_1.outputs[30].hide = True
    ____007_1.outputs[31].hide = True
    ____007_1.outputs[32].hide = True
    ____007_1.outputs[33].hide = True
    ____007_1.outputs[34].hide = True
    ____007_1.outputs[35].hide = True
    ____007_1.outputs[36].hide = True
    ____007_1.outputs[37].hide = True
    ____007_1.outputs[38].hide = True
    ____007_1.outputs[39].hide = True
    ____007_1.outputs[40].hide = True

    # Node 转接点.005
    ____005 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____005.name = "转接点.005"
    ____005.socket_idname = "NodeSocketFloat"
    # Node 组输入.012
    ____012 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____012.name = "组输入.012"
    ____012.outputs[0].hide = True
    ____012.outputs[1].hide = True
    ____012.outputs[2].hide = True
    ____012.outputs[3].hide = True
    ____012.outputs[4].hide = True
    ____012.outputs[5].hide = True
    ____012.outputs[6].hide = True
    ____012.outputs[7].hide = True
    ____012.outputs[9].hide = True
    ____012.outputs[10].hide = True
    ____012.outputs[11].hide = True
    ____012.outputs[12].hide = True
    ____012.outputs[13].hide = True
    ____012.outputs[14].hide = True
    ____012.outputs[15].hide = True
    ____012.outputs[16].hide = True
    ____012.outputs[17].hide = True
    ____012.outputs[18].hide = True
    ____012.outputs[19].hide = True
    ____012.outputs[20].hide = True
    ____012.outputs[21].hide = True
    ____012.outputs[22].hide = True
    ____012.outputs[23].hide = True
    ____012.outputs[24].hide = True
    ____012.outputs[25].hide = True
    ____012.outputs[26].hide = True
    ____012.outputs[27].hide = True
    ____012.outputs[28].hide = True
    ____012.outputs[29].hide = True
    ____012.outputs[30].hide = True
    ____012.outputs[31].hide = True
    ____012.outputs[32].hide = True
    ____012.outputs[33].hide = True
    ____012.outputs[34].hide = True
    ____012.outputs[35].hide = True
    ____012.outputs[36].hide = True
    ____012.outputs[37].hide = True
    ____012.outputs[38].hide = True
    ____012.outputs[39].hide = True
    ____012.outputs[40].hide = True

    # Node 运算.026
    ___026 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___026.name = "运算.026"
    ___026.hide = True
    ___026.operation = 'MULTIPLY'
    ___026.use_clamp = False

    # Node input_point_radius.012
    input_point_radius_012 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_012.name = "input_point_radius.012"
    input_point_radius_012.outputs[0].hide = True
    input_point_radius_012.outputs[1].hide = True
    input_point_radius_012.outputs[2].hide = True
    input_point_radius_012.outputs[3].hide = True
    input_point_radius_012.outputs[4].hide = True
    input_point_radius_012.outputs[5].hide = True
    input_point_radius_012.outputs[6].hide = True
    input_point_radius_012.outputs[7].hide = True
    input_point_radius_012.outputs[8].hide = True
    input_point_radius_012.outputs[9].hide = True
    input_point_radius_012.outputs[10].hide = True
    input_point_radius_012.outputs[11].hide = True
    input_point_radius_012.outputs[12].hide = True
    input_point_radius_012.outputs[13].hide = True
    input_point_radius_012.outputs[14].hide = True
    input_point_radius_012.outputs[15].hide = True
    input_point_radius_012.outputs[16].hide = True
    input_point_radius_012.outputs[17].hide = True
    input_point_radius_012.outputs[18].hide = True
    input_point_radius_012.outputs[19].hide = True
    input_point_radius_012.outputs[20].hide = True
    input_point_radius_012.outputs[21].hide = True
    input_point_radius_012.outputs[22].hide = True
    input_point_radius_012.outputs[23].hide = True
    input_point_radius_012.outputs[24].hide = True
    input_point_radius_012.outputs[25].hide = True
    input_point_radius_012.outputs[26].hide = True
    input_point_radius_012.outputs[27].hide = True
    input_point_radius_012.outputs[28].hide = True
    input_point_radius_012.outputs[29].hide = True
    input_point_radius_012.outputs[30].hide = True
    input_point_radius_012.outputs[31].hide = True
    input_point_radius_012.outputs[32].hide = True
    input_point_radius_012.outputs[33].hide = True
    input_point_radius_012.outputs[34].hide = True
    input_point_radius_012.outputs[35].hide = True
    input_point_radius_012.outputs[36].hide = True
    input_point_radius_012.outputs[37].hide = True
    input_point_radius_012.outputs[38].hide = True
    input_point_radius_012.outputs[40].hide = True

    # Node 矢量运算.014
    _____014 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____014.name = "矢量运算.014"
    _____014.operation = 'NORMALIZE'

    # Node 切换.004
    ___004 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___004.name = "切换.004"
    ___004.input_type = 'VECTOR'

    # Node 运算.024
    ___024 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___024.name = "运算.024"
    ___024.hide = True
    ___024.operation = 'EXPONENT'
    ___024.use_clamp = False

    # Node 运算.041
    ___041 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___041.name = "运算.041"
    ___041.hide = True
    ___041.operation = 'EXPONENT'
    ___041.use_clamp = False

    # Node 运算.042
    ___042 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___042.name = "运算.042"
    ___042.hide = True
    ___042.operation = 'EXPONENT'
    ___042.use_clamp = False

    # Node 群组.003
    ___003_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___003_1.name = "群组.003"
    ___003_1.node_tree = bpy.data.node_groups[node_tree_names[sigmod_g_1_node_group]]

    # Node 运算.035
    ___035 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___035.name = "运算.035"
    ___035.operation = 'MULTIPLY'
    ___035.use_clamp = False
    # Value_001
    ___035.inputs[1].default_value = 0.009999999776482582

    # Node 存储已命名属性.020
    ________020 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________020.name = "存储已命名属性.020"
    ________020.data_type = 'FLOAT'
    ________020.domain = 'POINT'
    # Selection
    ________020.inputs[1].default_value = True
    # Name
    ________020.inputs[2].default_value = "computeAlpha"

    # Node 实现实例.004
    _____004 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRealizeInstances")
    _____004.name = "实现实例.004"
    # Selection
    _____004.inputs[1].default_value = True
    # Realize All
    _____004.inputs[2].default_value = True
    # Depth
    _____004.inputs[3].default_value = 0

    # Node 转接点.010
    ____010 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____010.name = "转接点.010"
    ____010.socket_idname = "NodeSocketBool"
    # Node 转接点.017
    ____017 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____017.name = "转接点.017"
    ____017.socket_idname = "NodeSocketGeometry"
    # Node 转接点.018
    ____018 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____018.name = "转接点.018"
    ____018.socket_idname = "NodeSocketGeometry"
    # Node 转接点.019
    ____019 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____019.name = "转接点.019"
    ____019.socket_idname = "NodeSocketGeometry"
    # Node 转接点.020
    ____020 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____020.name = "转接点.020"
    ____020.socket_idname = "NodeSocketGeometry"
    # Node 重复输入
    _____1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRepeatInput")
    _____1.name = "重复输入"
    # Node 重复输出
    _____2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRepeatOutput")
    _____2.name = "重复输出"
    _____2.active_index = 1
    _____2.inspection_index = 0
    _____2.repeat_items.clear()
    # Create item "几何数据"
    _____2.repeat_items.new('GEOMETRY', "几何数据")
    # Create item "String"
    _____2.repeat_items.new('STRING', "String")
    # Item_1
    _____2.inputs[1].default_value = ""

    # Node 已命名属性.006
    ______006 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______006.name = "已命名属性.006"
    ______006.data_type = 'FLOAT'

    # Node 字符串
    ____1 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeInputString")
    ____1.name = "字符串"
    ____1.string = "f_rest_"

    # Node 合并字符串
    ______1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStringJoin")
    ______1.name = "合并字符串"
    # Delimiter
    ______1.inputs[0].default_value = ""

    # Node 数值 转换为 字符串
    __________ = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeValueToString")
    __________.name = "数值 转换为 字符串"
    __________.data_type = 'INT'

    # Node 整数运算
    _____3 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____3.name = "整数运算"
    _____3.operation = 'ADD'
    # Value_001
    _____3.inputs[1].default_value = 0

    # Node 整数运算.001
    _____001_3 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____001_3.name = "整数运算.001"
    _____001_3.operation = 'ADD'

    # Node 整数运算.002
    _____002_2 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____002_2.name = "整数运算.002"
    _____002_2.operation = 'ADD'

    # Node 数值 转换为 字符串.001
    ___________001 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeValueToString")
    ___________001.name = "数值 转换为 字符串.001"
    ___________001.data_type = 'INT'

    # Node 数值 转换为 字符串.002
    ___________002 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeValueToString")
    ___________002.name = "数值 转换为 字符串.002"
    ___________002.data_type = 'INT'

    # Node 已命名属性.007
    ______007 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______007.name = "已命名属性.007"
    ______007.data_type = 'FLOAT'

    # Node 合并字符串.001
    ______001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStringJoin")
    ______001.name = "合并字符串.001"
    # Delimiter
    ______001.inputs[0].default_value = ""

    # Node 已命名属性.008
    ______008 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______008.name = "已命名属性.008"
    ______008.data_type = 'FLOAT'

    # Node 合并字符串.002
    ______002 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStringJoin")
    ______002.name = "合并字符串.002"
    # Delimiter
    ______002.inputs[0].default_value = ""

    # Node 存储已命名属性.021
    ________021 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________021.name = "存储已命名属性.021"
    ________021.data_type = 'FLOAT_VECTOR'
    ________021.domain = 'POINT'
    # Selection
    ________021.inputs[1].default_value = True

    # Node 整数运算.004
    _____004_1 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____004_1.name = "整数运算.004"
    _____004_1.operation = 'ADD'
    # Value_001
    _____004_1.inputs[1].default_value = 1

    # Node 数值 转换为 字符串.003
    ___________003 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeValueToString")
    ___________003.name = "数值 转换为 字符串.003"
    ___________003.data_type = 'INT'

    # Node 字符串.001
    ____001_3 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeInputString")
    ____001_3.name = "字符串.001"
    ____001_3.string = "SH_"

    # Node 合并字符串.003
    ______003 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStringJoin")
    ______003.name = "合并字符串.003"
    # Delimiter
    ______003.inputs[0].default_value = ""

    # Node 合并 XYZ
    ___xyz = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz.name = "合并 XYZ"

    # Node 转接点.021
    ____021 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____021.name = "转接点.021"
    ____021.socket_idname = "NodeSocketString"
    # Node 已命名属性.009
    ______009 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______009.name = "已命名属性.009"
    ______009.data_type = 'FLOAT'
    # Name
    ______009.inputs[0].default_value = "f_dc_0"

    # Node 已命名属性.010
    ______010 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______010.name = "已命名属性.010"
    ______010.data_type = 'FLOAT'
    # Name
    ______010.inputs[0].default_value = "f_dc_1"

    # Node 已命名属性.011
    ______011 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______011.name = "已命名属性.011"
    ______011.data_type = 'FLOAT'
    # Name
    ______011.inputs[0].default_value = "f_dc_2"

    # Node 存储已命名属性.022
    ________022 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________022.name = "存储已命名属性.022"
    ________022.data_type = 'FLOAT_VECTOR'
    ________022.domain = 'POINT'
    # Selection
    ________022.inputs[1].default_value = True
    # Name
    ________022.inputs[2].default_value = "SH_0"

    # Node 合并 XYZ.001
    ___xyz_001 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_001.name = "合并 XYZ.001"

    # Node 删除几何体.003
    ______003_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDeleteGeometry")
    ______003_1.name = "删除几何体.003"
    ______003_1.domain = 'POINT'
    ______003_1.mode = 'ALL'

    # Node 物体信息.004
    _____004_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____004_2.name = "物体信息.004"
    _____004_2.transform_space = 'RELATIVE'
    # As Instance
    _____004_2.inputs[1].default_value = False

    # Node 矢量运算.003
    _____003 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____003.name = "矢量运算.003"
    _____003.hide = True
    _____003.operation = 'LENGTH'

    # Node 运算.036
    ___036 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___036.name = "运算.036"
    ___036.operation = 'GREATER_THAN'
    ___036.use_clamp = False
    # Value_001
    ___036.inputs[1].default_value = 1.0

    # Node 位置.007
    ___007 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputPosition")
    ___007.name = "位置.007"

    # Node 实现实例.003
    _____003_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRealizeInstances")
    _____003_1.name = "实现实例.003"
    # Selection
    _____003_1.inputs[1].default_value = True
    # Realize All
    _____003_1.inputs[2].default_value = True
    # Depth
    _____003_1.inputs[3].default_value = 0

    # Node 转接点.025
    ____025 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____025.name = "转接点.025"
    ____025.socket_idname = "NodeSocketGeometry"
    # Node 转接点.027
    ____027 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____027.name = "转接点.027"
    ____027.socket_idname = "NodeSocketGeometry"
    # Node 存储已命名属性.023
    ________023 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________023.name = "存储已命名属性.023"
    ________023.data_type = 'FLOAT_VECTOR'
    ________023.domain = 'POINT'
    # Selection
    ________023.inputs[1].default_value = True
    # Name
    ________023.inputs[2].default_value = "G_Rot"

    # Node 切换.006
    ___006 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___006.name = "切换.006"
    ___006.input_type = 'GEOMETRY'
    # Switch
    ___006.inputs[0].default_value = False

    # Node input_point_radius.014
    input_point_radius_014 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_014.name = "input_point_radius.014"
    input_point_radius_014.outputs[0].hide = True
    input_point_radius_014.outputs[1].hide = True
    input_point_radius_014.outputs[2].hide = True
    input_point_radius_014.outputs[3].hide = True
    input_point_radius_014.outputs[4].hide = True
    input_point_radius_014.outputs[5].hide = True
    input_point_radius_014.outputs[6].hide = True
    input_point_radius_014.outputs[7].hide = True
    input_point_radius_014.outputs[8].hide = True
    input_point_radius_014.outputs[9].hide = True
    input_point_radius_014.outputs[10].hide = True
    input_point_radius_014.outputs[11].hide = True
    input_point_radius_014.outputs[12].hide = True
    input_point_radius_014.outputs[13].hide = True
    input_point_radius_014.outputs[14].hide = True
    input_point_radius_014.outputs[15].hide = True
    input_point_radius_014.outputs[16].hide = True
    input_point_radius_014.outputs[17].hide = True
    input_point_radius_014.outputs[18].hide = True
    input_point_radius_014.outputs[19].hide = True
    input_point_radius_014.outputs[20].hide = True
    input_point_radius_014.outputs[21].hide = True
    input_point_radius_014.outputs[22].hide = True
    input_point_radius_014.outputs[23].hide = True
    input_point_radius_014.outputs[24].hide = True
    input_point_radius_014.outputs[25].hide = True
    input_point_radius_014.outputs[26].hide = True
    input_point_radius_014.outputs[27].hide = True
    input_point_radius_014.outputs[28].hide = True
    input_point_radius_014.outputs[29].hide = True
    input_point_radius_014.outputs[30].hide = True
    input_point_radius_014.outputs[31].hide = True
    input_point_radius_014.outputs[32].hide = True
    input_point_radius_014.outputs[33].hide = True
    input_point_radius_014.outputs[34].hide = True
    input_point_radius_014.outputs[35].hide = True
    input_point_radius_014.outputs[36].hide = True
    input_point_radius_014.outputs[37].hide = True
    input_point_radius_014.outputs[38].hide = True
    input_point_radius_014.outputs[39].hide = True
    input_point_radius_014.outputs[40].hide = True

    # Node Group Input.004
    group_input_004 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    group_input_004.name = "Group Input.004"
    group_input_004.outputs[0].hide = True
    group_input_004.outputs[1].hide = True
    group_input_004.outputs[2].hide = True
    group_input_004.outputs[3].hide = True
    group_input_004.outputs[4].hide = True
    group_input_004.outputs[5].hide = True
    group_input_004.outputs[6].hide = True
    group_input_004.outputs[7].hide = True
    group_input_004.outputs[8].hide = True
    group_input_004.outputs[9].hide = True
    group_input_004.outputs[10].hide = True
    group_input_004.outputs[11].hide = True
    group_input_004.outputs[12].hide = True
    group_input_004.outputs[13].hide = True
    group_input_004.outputs[14].hide = True
    group_input_004.outputs[16].hide = True
    group_input_004.outputs[17].hide = True
    group_input_004.outputs[18].hide = True
    group_input_004.outputs[19].hide = True
    group_input_004.outputs[20].hide = True
    group_input_004.outputs[21].hide = True
    group_input_004.outputs[22].hide = True
    group_input_004.outputs[23].hide = True
    group_input_004.outputs[24].hide = True
    group_input_004.outputs[25].hide = True
    group_input_004.outputs[26].hide = True
    group_input_004.outputs[27].hide = True
    group_input_004.outputs[28].hide = True
    group_input_004.outputs[29].hide = True
    group_input_004.outputs[30].hide = True
    group_input_004.outputs[31].hide = True
    group_input_004.outputs[32].hide = True
    group_input_004.outputs[33].hide = True
    group_input_004.outputs[34].hide = True
    group_input_004.outputs[35].hide = True
    group_input_004.outputs[36].hide = True
    group_input_004.outputs[37].hide = True
    group_input_004.outputs[38].hide = True
    group_input_004.outputs[39].hide = True
    group_input_004.outputs[40].hide = True

    # Node 运算.010
    ___010 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___010.name = "运算.010"
    ___010.hide = True
    ___010.operation = 'SUBTRACT'
    ___010.use_clamp = False

    # Node input_point_radius.017
    input_point_radius_017 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_017.name = "input_point_radius.017"
    input_point_radius_017.hide = True
    input_point_radius_017.outputs[0].hide = True
    input_point_radius_017.outputs[1].hide = True
    input_point_radius_017.outputs[2].hide = True
    input_point_radius_017.outputs[3].hide = True
    input_point_radius_017.outputs[4].hide = True
    input_point_radius_017.outputs[5].hide = True
    input_point_radius_017.outputs[6].hide = True
    input_point_radius_017.outputs[7].hide = True
    input_point_radius_017.outputs[8].hide = True
    input_point_radius_017.outputs[9].hide = True
    input_point_radius_017.outputs[10].hide = True
    input_point_radius_017.outputs[11].hide = True
    input_point_radius_017.outputs[12].hide = True
    input_point_radius_017.outputs[14].hide = True
    input_point_radius_017.outputs[15].hide = True
    input_point_radius_017.outputs[16].hide = True
    input_point_radius_017.outputs[17].hide = True
    input_point_radius_017.outputs[18].hide = True
    input_point_radius_017.outputs[19].hide = True
    input_point_radius_017.outputs[20].hide = True
    input_point_radius_017.outputs[21].hide = True
    input_point_radius_017.outputs[22].hide = True
    input_point_radius_017.outputs[23].hide = True
    input_point_radius_017.outputs[24].hide = True
    input_point_radius_017.outputs[25].hide = True
    input_point_radius_017.outputs[26].hide = True
    input_point_radius_017.outputs[27].hide = True
    input_point_radius_017.outputs[28].hide = True
    input_point_radius_017.outputs[29].hide = True
    input_point_radius_017.outputs[30].hide = True
    input_point_radius_017.outputs[31].hide = True
    input_point_radius_017.outputs[32].hide = True
    input_point_radius_017.outputs[33].hide = True
    input_point_radius_017.outputs[34].hide = True
    input_point_radius_017.outputs[35].hide = True
    input_point_radius_017.outputs[36].hide = True
    input_point_radius_017.outputs[37].hide = True
    input_point_radius_017.outputs[38].hide = True
    input_point_radius_017.outputs[39].hide = True
    input_point_radius_017.outputs[40].hide = True

    # Node 转接点.036
    ____036 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____036.name = "转接点.036"
    ____036.hide = True
    ____036.socket_idname = "NodeSocketInt"
    # Node 转接点.037
    ____037 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____037.name = "转接点.037"
    ____037.socket_idname = "NodeSocketInt"
    # Node 转接点.038
    ____038 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____038.name = "转接点.038"
    ____038.socket_idname = "NodeSocketInt"
    # Node 转接点.039
    ____039 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____039.name = "转接点.039"
    ____039.socket_idname = "NodeSocketInt"
    # Node 整数运算.003
    _____003_2 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____003_2.name = "整数运算.003"
    _____003_2.hide = True
    _____003_2.operation = 'ADD'
    # Value_001
    _____003_2.inputs[1].default_value = 1

    # Node 整数运算.005
    _____005 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____005.name = "整数运算.005"
    _____005.hide = True
    _____005.operation = 'MULTIPLY'

    # Node 整数运算.006
    _____006 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____006.name = "整数运算.006"
    _____006.hide = True
    _____006.operation = 'SUBTRACT'
    # Value_001
    _____006.inputs[1].default_value = 1

    # Node 整数运算.007
    _____007 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____007.name = "整数运算.007"
    _____007.hide = True
    _____007.operation = 'MULTIPLY'
    # Value_001
    _____007.inputs[1].default_value = 2

    # Node input_point_radius.018
    input_point_radius_018 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_018.name = "input_point_radius.018"
    input_point_radius_018.outputs[0].hide = True
    input_point_radius_018.outputs[1].hide = True
    input_point_radius_018.outputs[2].hide = True
    input_point_radius_018.outputs[3].hide = True
    input_point_radius_018.outputs[4].hide = True
    input_point_radius_018.outputs[5].hide = True
    input_point_radius_018.outputs[6].hide = True
    input_point_radius_018.outputs[7].hide = True
    input_point_radius_018.outputs[8].hide = True
    input_point_radius_018.outputs[9].hide = True
    input_point_radius_018.outputs[10].hide = True
    input_point_radius_018.outputs[11].hide = True
    input_point_radius_018.outputs[12].hide = True
    input_point_radius_018.outputs[13].hide = True
    input_point_radius_018.outputs[14].hide = True
    input_point_radius_018.outputs[15].hide = True
    input_point_radius_018.outputs[16].hide = True
    input_point_radius_018.outputs[17].hide = True
    input_point_radius_018.outputs[18].hide = True
    input_point_radius_018.outputs[19].hide = True
    input_point_radius_018.outputs[20].hide = True
    input_point_radius_018.outputs[21].hide = True
    input_point_radius_018.outputs[22].hide = True
    input_point_radius_018.outputs[23].hide = True
    input_point_radius_018.outputs[24].hide = True
    input_point_radius_018.outputs[25].hide = True
    input_point_radius_018.outputs[26].hide = True
    input_point_radius_018.outputs[27].hide = True
    input_point_radius_018.outputs[28].hide = True
    input_point_radius_018.outputs[29].hide = True
    input_point_radius_018.outputs[30].hide = True
    input_point_radius_018.outputs[31].hide = True
    input_point_radius_018.outputs[32].hide = True
    input_point_radius_018.outputs[33].hide = True
    input_point_radius_018.outputs[35].hide = True
    input_point_radius_018.outputs[36].hide = True
    input_point_radius_018.outputs[37].hide = True
    input_point_radius_018.outputs[38].hide = True
    input_point_radius_018.outputs[39].hide = True
    input_point_radius_018.outputs[40].hide = True

    # Node 切换.008
    ___008_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___008_1.name = "切换.008"
    ___008_1.input_type = 'GEOMETRY'

    # Node 转接点.022
    ____022 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____022.name = "转接点.022"
    ____022.mute = True
    ____022.socket_idname = "NodeSocketGeometry"
    # Node 转接点.023
    ____023 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____023.name = "转接点.023"
    ____023.socket_idname = "NodeSocketGeometry"
    # Node 菜单切换.003
    _____003_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____003_3.name = "菜单切换.003"
    _____003_3.active_index = 1
    _____003_3.data_type = 'FLOAT'
    _____003_3.enum_items.clear()
    _____003_3.enum_items.new("Fix")
    _____003_3.enum_items[0].description = ""
    _____003_3.enum_items.new("Auto")
    _____003_3.enum_items[1].description = ""
    _____003_3.enum_items.new("Max")
    _____003_3.enum_items[2].description = ""

    # Node input_point_radius.019
    input_point_radius_019 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_019.name = "input_point_radius.019"
    input_point_radius_019.outputs[0].hide = True
    input_point_radius_019.outputs[1].hide = True
    input_point_radius_019.outputs[2].hide = True
    input_point_radius_019.outputs[3].hide = True
    input_point_radius_019.outputs[4].hide = True
    input_point_radius_019.outputs[5].hide = True
    input_point_radius_019.outputs[6].hide = True
    input_point_radius_019.outputs[7].hide = True
    input_point_radius_019.outputs[8].hide = True
    input_point_radius_019.outputs[9].hide = True
    input_point_radius_019.outputs[10].hide = True
    input_point_radius_019.outputs[11].hide = True
    input_point_radius_019.outputs[12].hide = True
    input_point_radius_019.outputs[13].hide = True
    input_point_radius_019.outputs[14].hide = True
    input_point_radius_019.outputs[15].hide = True
    input_point_radius_019.outputs[16].hide = True
    input_point_radius_019.outputs[17].hide = True
    input_point_radius_019.outputs[18].hide = True
    input_point_radius_019.outputs[19].hide = True
    input_point_radius_019.outputs[20].hide = True
    input_point_radius_019.outputs[21].hide = True
    input_point_radius_019.outputs[22].hide = True
    input_point_radius_019.outputs[23].hide = True
    input_point_radius_019.outputs[24].hide = True
    input_point_radius_019.outputs[25].hide = True
    input_point_radius_019.outputs[26].hide = True
    input_point_radius_019.outputs[28].hide = True
    input_point_radius_019.outputs[29].hide = True
    input_point_radius_019.outputs[30].hide = True
    input_point_radius_019.outputs[31].hide = True
    input_point_radius_019.outputs[32].hide = True
    input_point_radius_019.outputs[33].hide = True
    input_point_radius_019.outputs[34].hide = True
    input_point_radius_019.outputs[35].hide = True
    input_point_radius_019.outputs[36].hide = True
    input_point_radius_019.outputs[37].hide = True
    input_point_radius_019.outputs[38].hide = True
    input_point_radius_019.outputs[39].hide = True
    input_point_radius_019.outputs[40].hide = True

    # Node 实例化于点上.005
    _______005 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInstanceOnPoints")
    _______005.name = "实例化于点上.005"
    _______005.inputs[1].hide = True
    _______005.inputs[3].hide = True
    _______005.inputs[4].hide = True
    # Selection
    _______005.inputs[1].default_value = True
    # Pick Instance
    _______005.inputs[3].default_value = False
    # Instance Index
    _______005.inputs[4].default_value = 0

    # Node 设置着色平滑.001
    _______001 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSetShadeSmooth")
    _______001.name = "设置着色平滑.001"
    _______001.domain = 'FACE'
    # Selection
    _______001.inputs[1].default_value = True
    # Shade Smooth
    _______001.inputs[2].default_value = False

    # Node 转接点.041
    ____041 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____041.name = "转接点.041"
    ____041.socket_idname = "NodeSocketGeometry"
    # Node 存储已命名属性.018
    ________018 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________018.name = "存储已命名属性.018"
    ________018.data_type = 'FLOAT_VECTOR'
    ________018.domain = 'POINT'
    # Selection
    ________018.inputs[1].default_value = True
    # Name
    ________018.inputs[2].default_value = "PPP"

    # Node 合并 XYZ.005
    ___xyz_005 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_005.label = "A0"
    ___xyz_005.name = "合并 XYZ.005"

    # Node 合并 XYZ.007
    ___xyz_007 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_007.label = "A1"
    ___xyz_007.name = "合并 XYZ.007"

    # Node 合并 XYZ.008
    ___xyz_008 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_008.label = "A2"
    ___xyz_008.name = "合并 XYZ.008"

    # Node 逆矩阵.002
    ____002 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeInvertMatrix")
    ____002.name = "逆矩阵.002"

    # Node 存储已命名属性.028
    ________028 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________028.name = "存储已命名属性.028"
    ________028.data_type = 'FLOAT_VECTOR'
    ________028.domain = 'POINT'
    # Selection
    ________028.inputs[1].default_value = True
    # Name
    ________028.inputs[2].default_value = "inv_L0"

    # Node 存储已命名属性.029
    ________029 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________029.name = "存储已命名属性.029"
    ________029.data_type = 'FLOAT_VECTOR'
    ________029.domain = 'POINT'
    # Selection
    ________029.inputs[1].default_value = True
    # Name
    ________029.inputs[2].default_value = "inv_L1"

    # Node 存储已命名属性.030
    ________030 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________030.name = "存储已命名属性.030"
    ________030.data_type = 'FLOAT_VECTOR'
    ________030.domain = 'POINT'
    # Selection
    ________030.inputs[1].default_value = True
    # Name
    ________030.inputs[2].default_value = "inv_L2"

    # Node 分离矩阵.001
    _____001_4 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeSeparateMatrix")
    _____001_4.name = "分离矩阵.001"

    # Node 转置矩阵.003
    _____003_4 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeTransposeMatrix")
    _____003_4.name = "转置矩阵.003"

    # Node 运算.056
    ___056 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___056.name = "运算.056"
    ___056.operation = 'MAXIMUM'
    ___056.use_clamp = False

    # Node 运算.057
    ___057 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___057.name = "运算.057"
    ___057.operation = 'MAXIMUM'
    ___057.use_clamp = False

    # Node 分离 XYZ
    ___xyz_1 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeSeparateXYZ")
    ___xyz_1.name = "分离 XYZ"

    # Node 删除几何体.007
    ______007_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDeleteGeometry")
    ______007_1.name = "删除几何体.007"
    ______007_1.domain = 'POINT'
    ______007_1.mode = 'ALL'

    # Node 运算.059
    ___059 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___059.name = "运算.059"
    ___059.hide = True
    ___059.operation = 'LESS_THAN'
    ___059.use_clamp = False

    # Node input_point_radius.020
    input_point_radius_020 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_020.name = "input_point_radius.020"
    input_point_radius_020.outputs[0].hide = True
    input_point_radius_020.outputs[1].hide = True
    input_point_radius_020.outputs[2].hide = True
    input_point_radius_020.outputs[3].hide = True
    input_point_radius_020.outputs[4].hide = True
    input_point_radius_020.outputs[5].hide = True
    input_point_radius_020.outputs[6].hide = True
    input_point_radius_020.outputs[7].hide = True
    input_point_radius_020.outputs[8].hide = True
    input_point_radius_020.outputs[9].hide = True
    input_point_radius_020.outputs[10].hide = True
    input_point_radius_020.outputs[11].hide = True
    input_point_radius_020.outputs[12].hide = True
    input_point_radius_020.outputs[13].hide = True
    input_point_radius_020.outputs[14].hide = True
    input_point_radius_020.outputs[15].hide = True
    input_point_radius_020.outputs[16].hide = True
    input_point_radius_020.outputs[17].hide = True
    input_point_radius_020.outputs[18].hide = True
    input_point_radius_020.outputs[19].hide = True
    input_point_radius_020.outputs[20].hide = True
    input_point_radius_020.outputs[21].hide = True
    input_point_radius_020.outputs[22].hide = True
    input_point_radius_020.outputs[23].hide = True
    input_point_radius_020.outputs[24].hide = True
    input_point_radius_020.outputs[25].hide = True
    input_point_radius_020.outputs[27].hide = True
    input_point_radius_020.outputs[28].hide = True
    input_point_radius_020.outputs[29].hide = True
    input_point_radius_020.outputs[30].hide = True
    input_point_radius_020.outputs[31].hide = True
    input_point_radius_020.outputs[32].hide = True
    input_point_radius_020.outputs[33].hide = True
    input_point_radius_020.outputs[34].hide = True
    input_point_radius_020.outputs[35].hide = True
    input_point_radius_020.outputs[36].hide = True
    input_point_radius_020.outputs[37].hide = True
    input_point_radius_020.outputs[38].hide = True
    input_point_radius_020.outputs[39].hide = True
    input_point_radius_020.outputs[40].hide = True

    # Node 菜单切换.004
    _____004_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____004_3.name = "菜单切换.004"
    _____004_3.active_index = 1
    _____004_3.data_type = 'BOOLEAN'
    _____004_3.enum_items.clear()
    _____004_3.enum_items.new("Col")
    _____004_3.enum_items[0].description = ""
    _____004_3.enum_items.new("SH")
    _____004_3.enum_items[1].description = ""
    # Item_0
    _____004_3.inputs[1].default_value = False
    # Item_3
    _____004_3.inputs[2].default_value = True

    # Node input_point_radius.021
    input_point_radius_021 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_021.name = "input_point_radius.021"
    input_point_radius_021.outputs[0].hide = True
    input_point_radius_021.outputs[1].hide = True
    input_point_radius_021.outputs[2].hide = True
    input_point_radius_021.outputs[3].hide = True
    input_point_radius_021.outputs[4].hide = True
    input_point_radius_021.outputs[5].hide = True
    input_point_radius_021.outputs[6].hide = True
    input_point_radius_021.outputs[7].hide = True
    input_point_radius_021.outputs[8].hide = True
    input_point_radius_021.outputs[9].hide = True
    input_point_radius_021.outputs[10].hide = True
    input_point_radius_021.outputs[11].hide = True
    input_point_radius_021.outputs[13].hide = True
    input_point_radius_021.outputs[14].hide = True
    input_point_radius_021.outputs[15].hide = True
    input_point_radius_021.outputs[16].hide = True
    input_point_radius_021.outputs[17].hide = True
    input_point_radius_021.outputs[18].hide = True
    input_point_radius_021.outputs[19].hide = True
    input_point_radius_021.outputs[20].hide = True
    input_point_radius_021.outputs[21].hide = True
    input_point_radius_021.outputs[22].hide = True
    input_point_radius_021.outputs[23].hide = True
    input_point_radius_021.outputs[24].hide = True
    input_point_radius_021.outputs[25].hide = True
    input_point_radius_021.outputs[26].hide = True
    input_point_radius_021.outputs[27].hide = True
    input_point_radius_021.outputs[28].hide = True
    input_point_radius_021.outputs[29].hide = True
    input_point_radius_021.outputs[30].hide = True
    input_point_radius_021.outputs[31].hide = True
    input_point_radius_021.outputs[32].hide = True
    input_point_radius_021.outputs[33].hide = True
    input_point_radius_021.outputs[34].hide = True
    input_point_radius_021.outputs[35].hide = True
    input_point_radius_021.outputs[36].hide = True
    input_point_radius_021.outputs[37].hide = True
    input_point_radius_021.outputs[38].hide = True
    input_point_radius_021.outputs[39].hide = True
    input_point_radius_021.outputs[40].hide = True

    # Node 存储已命名属性.026
    ________026 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________026.name = "存储已命名属性.026"
    ________026.data_type = 'FLOAT_VECTOR'
    ________026.domain = 'POINT'
    # Selection
    ________026.inputs[1].default_value = True
    # Name
    ________026.inputs[2].default_value = "SH_0"

    # Node 已命名属性.032
    ______032 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______032.name = "已命名属性.032"
    ______032.data_type = 'FLOAT_VECTOR'
    # Name
    ______032.inputs[0].default_value = "Col"

    # Node 菜单切换.005
    _____005_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____005_1.name = "菜单切换.005"
    _____005_1.active_index = 2
    _____005_1.data_type = 'INT'
    _____005_1.enum_items.clear()
    _____005_1.enum_items.new("Gaussion")
    _____005_1.enum_items[0].description = ""
    _____005_1.enum_items.new("Ring")
    _____005_1.enum_items[1].description = ""
    _____005_1.enum_items.new("Wireframe")
    _____005_1.enum_items[2].description = ""
    _____005_1.enum_items.new("Freestyle")
    _____005_1.enum_items[3].description = ""
    # Item_4
    _____005_1.inputs[1].default_value = 0
    # Item_7
    _____005_1.inputs[2].default_value = 1
    # Item_6
    _____005_1.inputs[3].default_value = 2
    # Item_5
    _____005_1.inputs[4].default_value = 3

    # Node input_point_radius.022
    input_point_radius_022 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_022.name = "input_point_radius.022"
    input_point_radius_022.outputs[0].hide = True
    input_point_radius_022.outputs[1].hide = True
    input_point_radius_022.outputs[2].hide = True
    input_point_radius_022.outputs[3].hide = True
    input_point_radius_022.outputs[4].hide = True
    input_point_radius_022.outputs[5].hide = True
    input_point_radius_022.outputs[6].hide = True
    input_point_radius_022.outputs[7].hide = True
    input_point_radius_022.outputs[8].hide = True
    input_point_radius_022.outputs[9].hide = True
    input_point_radius_022.outputs[10].hide = True
    input_point_radius_022.outputs[11].hide = True
    input_point_radius_022.outputs[12].hide = True
    input_point_radius_022.outputs[13].hide = True
    input_point_radius_022.outputs[14].hide = True
    input_point_radius_022.outputs[15].hide = True
    input_point_radius_022.outputs[16].hide = True
    input_point_radius_022.outputs[17].hide = True
    input_point_radius_022.outputs[18].hide = True
    input_point_radius_022.outputs[19].hide = True
    input_point_radius_022.outputs[20].hide = True
    input_point_radius_022.outputs[21].hide = True
    input_point_radius_022.outputs[22].hide = True
    input_point_radius_022.outputs[23].hide = True
    input_point_radius_022.outputs[24].hide = True
    input_point_radius_022.outputs[25].hide = True
    input_point_radius_022.outputs[26].hide = True
    input_point_radius_022.outputs[27].hide = True
    input_point_radius_022.outputs[28].hide = True
    input_point_radius_022.outputs[29].hide = True
    input_point_radius_022.outputs[30].hide = True
    input_point_radius_022.outputs[31].hide = True
    input_point_radius_022.outputs[33].hide = True
    input_point_radius_022.outputs[34].hide = True
    input_point_radius_022.outputs[35].hide = True
    input_point_radius_022.outputs[36].hide = True
    input_point_radius_022.outputs[37].hide = True
    input_point_radius_022.outputs[38].hide = True
    input_point_radius_022.outputs[39].hide = True
    input_point_radius_022.outputs[40].hide = True

    # Node 转接点
    ____2 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____2.name = "转接点"
    ____2.socket_idname = "NodeSocketGeometry"
    # Node 组输入.002
    ____002_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____002_1.name = "组输入.002"
    ____002_1.outputs[0].hide = True
    ____002_1.outputs[1].hide = True
    ____002_1.outputs[2].hide = True
    ____002_1.outputs[3].hide = True
    ____002_1.outputs[4].hide = True
    ____002_1.outputs[5].hide = True
    ____002_1.outputs[6].hide = True
    ____002_1.outputs[7].hide = True
    ____002_1.outputs[8].hide = True
    ____002_1.outputs[9].hide = True
    ____002_1.outputs[10].hide = True
    ____002_1.outputs[12].hide = True
    ____002_1.outputs[13].hide = True
    ____002_1.outputs[14].hide = True
    ____002_1.outputs[15].hide = True
    ____002_1.outputs[16].hide = True
    ____002_1.outputs[17].hide = True
    ____002_1.outputs[18].hide = True
    ____002_1.outputs[19].hide = True
    ____002_1.outputs[20].hide = True
    ____002_1.outputs[21].hide = True
    ____002_1.outputs[22].hide = True
    ____002_1.outputs[23].hide = True
    ____002_1.outputs[24].hide = True
    ____002_1.outputs[25].hide = True
    ____002_1.outputs[26].hide = True
    ____002_1.outputs[27].hide = True
    ____002_1.outputs[28].hide = True
    ____002_1.outputs[29].hide = True
    ____002_1.outputs[30].hide = True
    ____002_1.outputs[31].hide = True
    ____002_1.outputs[32].hide = True
    ____002_1.outputs[33].hide = True
    ____002_1.outputs[34].hide = True
    ____002_1.outputs[35].hide = True
    ____002_1.outputs[36].hide = True
    ____002_1.outputs[37].hide = True
    ____002_1.outputs[38].hide = True
    ____002_1.outputs[39].hide = True
    ____002_1.outputs[40].hide = True

    # Node 矢量运算.008
    _____008 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____008.name = "矢量运算.008"
    _____008.hide = True
    _____008.operation = 'SUBTRACT'

    # Node 矢量运算.009
    _____009 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____009.name = "矢量运算.009"
    _____009.hide = True
    _____009.operation = 'DIVIDE'

    # Node 四元数 转换为 旋转.002
    ___________002_1 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeQuaternionToRotation")
    ___________002_1.name = "四元数 转换为 旋转.002"

    # Node 对偶网格
    _____4 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDualMesh")
    _____4.name = "对偶网格"
    # Keep Boundaries
    _____4.inputs[1].default_value = False

    # Node 整数运算.008
    _____008_1 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____008_1.name = "整数运算.008"
    _____008_1.hide = True
    _____008_1.operation = 'ADD'

    # Node 组输入.013
    ____013 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____013.name = "组输入.013"
    ____013.outputs[0].hide = True
    ____013.outputs[1].hide = True
    ____013.outputs[2].hide = True
    ____013.outputs[3].hide = True
    ____013.outputs[4].hide = True
    ____013.outputs[5].hide = True
    ____013.outputs[6].hide = True
    ____013.outputs[7].hide = True
    ____013.outputs[8].hide = True
    ____013.outputs[9].hide = True
    ____013.outputs[10].hide = True
    ____013.outputs[11].hide = True
    ____013.outputs[12].hide = True
    ____013.outputs[13].hide = True
    ____013.outputs[14].hide = True
    ____013.outputs[15].hide = True
    ____013.outputs[17].hide = True
    ____013.outputs[18].hide = True
    ____013.outputs[19].hide = True
    ____013.outputs[20].hide = True
    ____013.outputs[21].hide = True
    ____013.outputs[22].hide = True
    ____013.outputs[23].hide = True
    ____013.outputs[24].hide = True
    ____013.outputs[25].hide = True
    ____013.outputs[26].hide = True
    ____013.outputs[27].hide = True
    ____013.outputs[28].hide = True
    ____013.outputs[29].hide = True
    ____013.outputs[30].hide = True
    ____013.outputs[31].hide = True
    ____013.outputs[32].hide = True
    ____013.outputs[33].hide = True
    ____013.outputs[34].hide = True
    ____013.outputs[35].hide = True
    ____013.outputs[36].hide = True
    ____013.outputs[37].hide = True
    ____013.outputs[38].hide = True
    ____013.outputs[39].hide = True
    ____013.outputs[40].hide = True

    # Node 组输入.014
    ____014 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____014.name = "组输入.014"
    ____014.outputs[0].hide = True
    ____014.outputs[1].hide = True
    ____014.outputs[2].hide = True
    ____014.outputs[3].hide = True
    ____014.outputs[4].hide = True
    ____014.outputs[5].hide = True
    ____014.outputs[6].hide = True
    ____014.outputs[7].hide = True
    ____014.outputs[8].hide = True
    ____014.outputs[9].hide = True
    ____014.outputs[10].hide = True
    ____014.outputs[11].hide = True
    ____014.outputs[12].hide = True
    ____014.outputs[13].hide = True
    ____014.outputs[14].hide = True
    ____014.outputs[15].hide = True
    ____014.outputs[16].hide = True
    ____014.outputs[17].hide = True
    ____014.outputs[18].hide = True
    ____014.outputs[19].hide = True
    ____014.outputs[21].hide = True
    ____014.outputs[22].hide = True
    ____014.outputs[23].hide = True
    ____014.outputs[24].hide = True
    ____014.outputs[25].hide = True
    ____014.outputs[26].hide = True
    ____014.outputs[27].hide = True
    ____014.outputs[28].hide = True
    ____014.outputs[29].hide = True
    ____014.outputs[30].hide = True
    ____014.outputs[31].hide = True
    ____014.outputs[32].hide = True
    ____014.outputs[33].hide = True
    ____014.outputs[34].hide = True
    ____014.outputs[35].hide = True
    ____014.outputs[36].hide = True
    ____014.outputs[37].hide = True
    ____014.outputs[38].hide = True
    ____014.outputs[39].hide = True
    ____014.outputs[40].hide = True

    # Node 转接点.051
    ____051 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____051.name = "转接点.051"
    ____051.socket_idname = "NodeSocketFloat"
    # Node 矢量运算.011
    _____011 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____011.label = "C0"
    _____011.name = "矢量运算.011"
    _____011.operation = 'SCALE'
    # Scale
    _____011.inputs[3].default_value = 0.282094806432724

    # Node 矢量运算.016
    _____016 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____016.name = "矢量运算.016"
    _____016.operation = 'SCALE'

    # Node 矢量运算.017
    _____017 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____017.label = "C1"
    _____017.name = "矢量运算.017"
    _____017.operation = 'SCALE'
    # Scale
    _____017.inputs[3].default_value = 0.48860251903533936

    # Node 矢量运算.018
    _____018 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____018.name = "矢量运算.018"
    _____018.operation = 'SCALE'

    # Node 矢量运算.042
    _____042 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____042.label = "C1"
    _____042.name = "矢量运算.042"
    _____042.operation = 'SCALE'
    # Scale
    _____042.inputs[3].default_value = 0.48860251903533936

    # Node 矢量运算.044
    _____044 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____044.name = "矢量运算.044"
    _____044.operation = 'SCALE'

    # Node 矢量运算.045
    _____045 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____045.label = "C1"
    _____045.name = "矢量运算.045"
    _____045.operation = 'SCALE'
    # Scale
    _____045.inputs[3].default_value = 0.48860251903533936

    # Node 矢量运算.019
    _____019 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____019.name = "矢量运算.019"
    _____019.operation = 'SCALE'

    # Node 矢量运算.043
    _____043 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____043.label = "C20"
    _____043.name = "矢量运算.043"
    _____043.operation = 'SCALE'
    # Scale
    _____043.inputs[3].default_value = 1.0925484895706177

    # Node 矢量运算.046
    _____046 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____046.name = "矢量运算.046"
    _____046.operation = 'SCALE'

    # Node 矢量运算.047
    _____047 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____047.label = "C21"
    _____047.name = "矢量运算.047"
    _____047.operation = 'SCALE'
    # Scale
    _____047.inputs[3].default_value = -1.0925484895706177

    # Node 矢量运算.048
    _____048 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____048.name = "矢量运算.048"
    _____048.operation = 'SCALE'

    # Node 矢量运算.049
    _____049 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____049.label = "C22"
    _____049.name = "矢量运算.049"
    _____049.operation = 'SCALE'
    # Scale
    _____049.inputs[3].default_value = 0.31539157032966614

    # Node 运算.044
    ___044 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___044.name = "运算.044"
    ___044.operation = 'MULTIPLY'
    ___044.use_clamp = False
    # Value_001
    ___044.inputs[1].default_value = 2.0

    # Node 运算.058
    ___058 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___058.name = "运算.058"
    ___058.operation = 'SUBTRACT'
    ___058.use_clamp = False

    # Node 运算.061
    ___061 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___061.name = "运算.061"
    ___061.operation = 'SUBTRACT'
    ___061.use_clamp = False

    # Node 矢量运算.050
    _____050 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____050.name = "矢量运算.050"
    _____050.operation = 'SCALE'

    # Node 矢量运算.051
    _____051 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____051.label = "C23"
    _____051.name = "矢量运算.051"
    _____051.operation = 'SCALE'
    # Scale
    _____051.inputs[3].default_value = -1.0925484895706177

    # Node 矢量运算.052
    _____052 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____052.name = "矢量运算.052"
    _____052.operation = 'SCALE'

    # Node 矢量运算.053
    _____053 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____053.label = "C24"
    _____053.name = "矢量运算.053"
    _____053.operation = 'SCALE'
    # Scale
    _____053.inputs[3].default_value = 0.5462742447853088

    # Node 运算.062
    ___062 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___062.name = "运算.062"
    ___062.operation = 'SUBTRACT'
    ___062.use_clamp = False

    # Node 矢量运算.020
    _____020 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____020.name = "矢量运算.020"
    _____020.operation = 'SUBTRACT'
    # Vector
    _____020.inputs[0].default_value = (0.0, 0.0, 0.0)

    # Node 矢量运算.021
    _____021 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____021.name = "矢量运算.021"
    _____021.operation = 'SUBTRACT'

    # Node 矢量运算.054
    _____054 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____054.name = "矢量运算.054"
    _____054.operation = 'ADD'

    # Node 矢量运算.055
    _____055 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____055.name = "矢量运算.055"
    _____055.operation = 'ADD'

    # Node 矢量运算.057
    _____057 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____057.name = "矢量运算.057"
    _____057.operation = 'ADD'

    # Node 矢量运算.058
    _____058 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____058.name = "矢量运算.058"
    _____058.operation = 'ADD'

    # Node 矢量运算.059
    _____059 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____059.name = "矢量运算.059"
    _____059.operation = 'ADD'

    # Node 矢量运算.061
    _____061 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____061.name = "矢量运算.061"
    _____061.operation = 'SCALE'

    # Node 矢量运算.062
    _____062 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____062.label = "C30"
    _____062.name = "矢量运算.062"
    _____062.operation = 'SCALE'
    # Scale
    _____062.inputs[3].default_value = -0.5900436043739319

    # Node 运算.063
    ___063 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___063.name = "运算.063"
    ___063.operation = 'MULTIPLY'
    ___063.use_clamp = False
    # Value_001
    ___063.inputs[1].default_value = 3.0

    # Node 运算.064
    ___064 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___064.name = "运算.064"
    ___064.operation = 'SUBTRACT'
    ___064.use_clamp = False

    # Node 运算.065
    ___065 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___065.name = "运算.065"
    ___065.operation = 'MULTIPLY'
    ___065.use_clamp = False

    # Node 矢量运算.063
    _____063 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____063.name = "矢量运算.063"
    _____063.operation = 'SCALE'

    # Node 矢量运算.064
    _____064 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____064.label = "C31"
    _____064.name = "矢量运算.064"
    _____064.operation = 'SCALE'
    # Scale
    _____064.inputs[3].default_value = 2.890611410140991

    # Node 运算.066
    ___066 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___066.name = "运算.066"
    ___066.operation = 'MULTIPLY'
    ___066.use_clamp = False

    # Node 矢量运算.065
    _____065 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____065.name = "矢量运算.065"
    _____065.operation = 'SCALE'

    # Node 矢量运算.066
    _____066 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____066.label = "C32"
    _____066.name = "矢量运算.066"
    _____066.operation = 'SCALE'
    # Scale
    _____066.inputs[3].default_value = -0.4570457935333252

    # Node 运算.067
    ___067 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___067.name = "运算.067"
    ___067.operation = 'MULTIPLY'
    ___067.use_clamp = False
    # Value_001
    ___067.inputs[1].default_value = 4.0

    # Node 运算.068
    ___068 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___068.name = "运算.068"
    ___068.operation = 'SUBTRACT'
    ___068.use_clamp = False

    # Node 运算.069
    ___069 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___069.name = "运算.069"
    ___069.operation = 'MULTIPLY'
    ___069.use_clamp = False

    # Node 运算.070
    ___070 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___070.name = "运算.070"
    ___070.operation = 'MULTIPLY'
    ___070.use_clamp = False

    # Node 矢量运算.067
    _____067 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____067.name = "矢量运算.067"
    _____067.operation = 'SCALE'

    # Node 矢量运算.068
    _____068 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____068.label = "C33"
    _____068.name = "矢量运算.068"
    _____068.operation = 'SCALE'
    # Scale
    _____068.inputs[3].default_value = 0.37317633628845215

    # Node 运算.071
    ___071 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___071.name = "运算.071"
    ___071.operation = 'MULTIPLY'
    ___071.use_clamp = False
    # Value_001
    ___071.inputs[1].default_value = 2.0

    # Node 运算.072
    ___072 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___072.name = "运算.072"
    ___072.operation = 'SUBTRACT'
    ___072.use_clamp = False

    # Node 运算.073
    ___073 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___073.name = "运算.073"
    ___073.operation = 'SUBTRACT'
    ___073.use_clamp = False

    # Node 运算.074
    ___074 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___074.name = "运算.074"
    ___074.operation = 'MULTIPLY'
    ___074.use_clamp = False
    # Value_001
    ___074.inputs[1].default_value = 3.0

    # Node 运算.075
    ___075 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___075.name = "运算.075"
    ___075.operation = 'MULTIPLY'
    ___075.use_clamp = False
    # Value_001
    ___075.inputs[1].default_value = 3.0

    # Node 运算.076
    ___076 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___076.name = "运算.076"
    ___076.operation = 'MULTIPLY'
    ___076.use_clamp = False

    # Node 矢量运算.069
    _____069 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____069.name = "矢量运算.069"
    _____069.operation = 'SCALE'

    # Node 矢量运算.070
    _____070 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____070.label = "C34"
    _____070.name = "矢量运算.070"
    _____070.operation = 'SCALE'
    # Scale
    _____070.inputs[3].default_value = -0.4570457935333252

    # Node 运算.077
    ___077 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___077.name = "运算.077"
    ___077.operation = 'MULTIPLY'
    ___077.use_clamp = False
    # Value_001
    ___077.inputs[1].default_value = 4.0

    # Node 运算.078
    ___078 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___078.name = "运算.078"
    ___078.operation = 'SUBTRACT'
    ___078.use_clamp = False

    # Node 运算.079
    ___079 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___079.name = "运算.079"
    ___079.operation = 'MULTIPLY'
    ___079.use_clamp = False

    # Node 运算.080
    ___080 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___080.name = "运算.080"
    ___080.operation = 'MULTIPLY'
    ___080.use_clamp = False

    # Node 矢量运算.071
    _____071 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____071.name = "矢量运算.071"
    _____071.operation = 'SCALE'

    # Node 矢量运算.072
    _____072 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____072.label = "C35"
    _____072.name = "矢量运算.072"
    _____072.operation = 'SCALE'
    # Scale
    _____072.inputs[3].default_value = 1.4453057050704956

    # Node 运算.081
    ___081 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___081.name = "运算.081"
    ___081.operation = 'SUBTRACT'
    ___081.use_clamp = False

    # Node 运算.082
    ___082 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___082.name = "运算.082"
    ___082.operation = 'MULTIPLY'
    ___082.use_clamp = False

    # Node 矢量运算.073
    _____073 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____073.name = "矢量运算.073"
    _____073.operation = 'SCALE'

    # Node 矢量运算.074
    _____074 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____074.label = "C36"
    _____074.name = "矢量运算.074"
    _____074.operation = 'SCALE'
    # Scale
    _____074.inputs[3].default_value = -0.5900436043739319

    # Node 运算.083
    ___083 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___083.name = "运算.083"
    ___083.operation = 'SUBTRACT'
    ___083.use_clamp = False

    # Node 运算.084
    ___084 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___084.name = "运算.084"
    ___084.operation = 'MULTIPLY'
    ___084.use_clamp = False

    # Node 运算.085
    ___085 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___085.name = "运算.085"
    ___085.operation = 'MULTIPLY'
    ___085.use_clamp = False
    # Value_001
    ___085.inputs[1].default_value = 3.0

    # Node 矢量运算.075
    _____075 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____075.name = "矢量运算.075"
    _____075.operation = 'ADD'

    # Node 矢量运算.077
    _____077 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____077.name = "矢量运算.077"
    _____077.operation = 'ADD'

    # Node 矢量运算.078
    _____078 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____078.name = "矢量运算.078"
    _____078.operation = 'ADD'

    # Node 矢量运算.079
    _____079 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____079.name = "矢量运算.079"
    _____079.operation = 'ADD'

    # Node 矢量运算.080
    _____080 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____080.name = "矢量运算.080"
    _____080.operation = 'ADD'

    # Node 矢量运算.081
    _____081 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____081.name = "矢量运算.081"
    _____081.operation = 'ADD'

    # Node 已命名属性.028
    ______028 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______028.name = "已命名属性.028"
    ______028.data_type = 'FLOAT_VECTOR'
    # Name
    ______028.inputs[0].default_value = "SH_0"

    # Node 已命名属性.031
    ______031 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______031.name = "已命名属性.031"
    ______031.data_type = 'FLOAT_VECTOR'
    # Name
    ______031.inputs[0].default_value = "SH_1"

    # Node 已命名属性.033
    ______033 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______033.name = "已命名属性.033"
    ______033.data_type = 'FLOAT_VECTOR'
    # Name
    ______033.inputs[0].default_value = "SH_2"

    # Node 已命名属性.034
    ______034 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______034.name = "已命名属性.034"
    ______034.data_type = 'FLOAT_VECTOR'
    # Name
    ______034.inputs[0].default_value = "SH_3"

    # Node 已命名属性.035
    ______035 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______035.name = "已命名属性.035"
    ______035.data_type = 'FLOAT_VECTOR'
    # Name
    ______035.inputs[0].default_value = "SH_4"

    # Node 已命名属性.036
    ______036 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______036.name = "已命名属性.036"
    ______036.data_type = 'FLOAT_VECTOR'
    # Name
    ______036.inputs[0].default_value = "SH_5"

    # Node 已命名属性.037
    ______037 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______037.name = "已命名属性.037"
    ______037.data_type = 'FLOAT_VECTOR'
    # Name
    ______037.inputs[0].default_value = "SH_6"

    # Node 已命名属性.038
    ______038 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______038.name = "已命名属性.038"
    ______038.data_type = 'FLOAT_VECTOR'
    # Name
    ______038.inputs[0].default_value = "SH_7"

    # Node 已命名属性.039
    ______039 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______039.name = "已命名属性.039"
    ______039.data_type = 'FLOAT_VECTOR'
    # Name
    ______039.inputs[0].default_value = "SH_8"

    # Node 已命名属性.040
    ______040 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______040.name = "已命名属性.040"
    ______040.data_type = 'FLOAT_VECTOR'
    # Name
    ______040.inputs[0].default_value = "SH_9"

    # Node 已命名属性.041
    ______041 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______041.name = "已命名属性.041"
    ______041.data_type = 'FLOAT_VECTOR'
    # Name
    ______041.inputs[0].default_value = "SH_10"

    # Node 已命名属性.042
    ______042 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______042.name = "已命名属性.042"
    ______042.data_type = 'FLOAT_VECTOR'
    # Name
    ______042.inputs[0].default_value = "SH_11"

    # Node 已命名属性.043
    ______043 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______043.name = "已命名属性.043"
    ______043.data_type = 'FLOAT_VECTOR'
    # Name
    ______043.inputs[0].default_value = "SH_12"

    # Node 已命名属性.044
    ______044 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______044.name = "已命名属性.044"
    ______044.data_type = 'FLOAT_VECTOR'
    # Name
    ______044.inputs[0].default_value = "SH_13"

    # Node 已命名属性.045
    ______045 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______045.name = "已命名属性.045"
    ______045.data_type = 'FLOAT_VECTOR'
    # Name
    ______045.inputs[0].default_value = "SH_14"

    # Node 已命名属性.046
    ______046 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______046.name = "已命名属性.046"
    ______046.data_type = 'FLOAT_VECTOR'
    # Name
    ______046.inputs[0].default_value = "SH_15"

    # Node 群组.004
    ___004_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___004_1.name = "群组.004"
    ___004_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.005
    ___005 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___005.name = "群组.005"
    ___005.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.007
    ___007_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___007_1.name = "群组.007"
    ___007_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.008
    ___008_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___008_2.name = "群组.008"
    ___008_2.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.009
    ___009_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___009_1.name = "群组.009"
    ___009_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.010
    ___010_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___010_1.name = "群组.010"
    ___010_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.011
    ___011 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___011.name = "群组.011"
    ___011.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.012
    ___012_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___012_1.name = "群组.012"
    ___012_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.013
    ___013_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___013_1.name = "群组.013"
    ___013_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.014
    ___014_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___014_1.name = "群组.014"
    ___014_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.015
    ___015_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___015_1.name = "群组.015"
    ___015_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.016
    ___016_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___016_1.name = "群组.016"
    ___016_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.017
    ___017_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___017_1.name = "群组.017"
    ___017_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.018
    ___018_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___018_1.name = "群组.018"
    ___018_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 群组.019
    ___019 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___019.name = "群组.019"
    ___019.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 存储已命名属性.032
    ________032 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________032.name = "存储已命名属性.032"
    ________032.data_type = 'FLOAT_VECTOR'
    ________032.domain = 'POINT'
    # Selection
    ________032.inputs[1].default_value = True
    # Name
    ________032.inputs[2].default_value = "Precompute"

    # Node 转接点.003
    ____003_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____003_1.name = "转接点.003"
    ____003_1.socket_idname = "NodeSocketGeometry"
    # Node 切换.010
    ___010_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___010_2.name = "切换.010"
    ___010_2.input_type = 'GEOMETRY'

    # Node input_point_radius.023
    input_point_radius_023 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_023.name = "input_point_radius.023"
    input_point_radius_023.outputs[0].hide = True
    input_point_radius_023.outputs[2].hide = True
    input_point_radius_023.outputs[3].hide = True
    input_point_radius_023.outputs[4].hide = True
    input_point_radius_023.outputs[5].hide = True
    input_point_radius_023.outputs[6].hide = True
    input_point_radius_023.outputs[7].hide = True
    input_point_radius_023.outputs[8].hide = True
    input_point_radius_023.outputs[9].hide = True
    input_point_radius_023.outputs[10].hide = True
    input_point_radius_023.outputs[11].hide = True
    input_point_radius_023.outputs[12].hide = True
    input_point_radius_023.outputs[13].hide = True
    input_point_radius_023.outputs[14].hide = True
    input_point_radius_023.outputs[15].hide = True
    input_point_radius_023.outputs[16].hide = True
    input_point_radius_023.outputs[17].hide = True
    input_point_radius_023.outputs[18].hide = True
    input_point_radius_023.outputs[19].hide = True
    input_point_radius_023.outputs[20].hide = True
    input_point_radius_023.outputs[21].hide = True
    input_point_radius_023.outputs[22].hide = True
    input_point_radius_023.outputs[23].hide = True
    input_point_radius_023.outputs[24].hide = True
    input_point_radius_023.outputs[25].hide = True
    input_point_radius_023.outputs[26].hide = True
    input_point_radius_023.outputs[27].hide = True
    input_point_radius_023.outputs[28].hide = True
    input_point_radius_023.outputs[29].hide = True
    input_point_radius_023.outputs[30].hide = True
    input_point_radius_023.outputs[31].hide = True
    input_point_radius_023.outputs[32].hide = True
    input_point_radius_023.outputs[33].hide = True
    input_point_radius_023.outputs[34].hide = True
    input_point_radius_023.outputs[35].hide = True
    input_point_radius_023.outputs[36].hide = True
    input_point_radius_023.outputs[37].hide = True
    input_point_radius_023.outputs[38].hide = True
    input_point_radius_023.outputs[39].hide = True
    input_point_radius_023.outputs[40].hide = True

    # Node input_point_radius.024
    input_point_radius_024 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_024.name = "input_point_radius.024"
    input_point_radius_024.outputs[0].hide = True
    input_point_radius_024.outputs[1].hide = True
    input_point_radius_024.outputs[2].hide = True
    input_point_radius_024.outputs[4].hide = True
    input_point_radius_024.outputs[5].hide = True
    input_point_radius_024.outputs[6].hide = True
    input_point_radius_024.outputs[7].hide = True
    input_point_radius_024.outputs[8].hide = True
    input_point_radius_024.outputs[9].hide = True
    input_point_radius_024.outputs[10].hide = True
    input_point_radius_024.outputs[11].hide = True
    input_point_radius_024.outputs[12].hide = True
    input_point_radius_024.outputs[13].hide = True
    input_point_radius_024.outputs[14].hide = True
    input_point_radius_024.outputs[15].hide = True
    input_point_radius_024.outputs[16].hide = True
    input_point_radius_024.outputs[17].hide = True
    input_point_radius_024.outputs[18].hide = True
    input_point_radius_024.outputs[19].hide = True
    input_point_radius_024.outputs[20].hide = True
    input_point_radius_024.outputs[21].hide = True
    input_point_radius_024.outputs[22].hide = True
    input_point_radius_024.outputs[23].hide = True
    input_point_radius_024.outputs[24].hide = True
    input_point_radius_024.outputs[25].hide = True
    input_point_radius_024.outputs[26].hide = True
    input_point_radius_024.outputs[27].hide = True
    input_point_radius_024.outputs[28].hide = True
    input_point_radius_024.outputs[29].hide = True
    input_point_radius_024.outputs[30].hide = True
    input_point_radius_024.outputs[31].hide = True
    input_point_radius_024.outputs[32].hide = True
    input_point_radius_024.outputs[33].hide = True
    input_point_radius_024.outputs[34].hide = True
    input_point_radius_024.outputs[35].hide = True
    input_point_radius_024.outputs[36].hide = True
    input_point_radius_024.outputs[37].hide = True
    input_point_radius_024.outputs[38].hide = True
    input_point_radius_024.outputs[39].hide = True
    input_point_radius_024.outputs[40].hide = True

    # Node 自身物体
    _____5 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSelfObject")
    _____5.name = "自身物体"

    # Node 物体信息.006
    _____006_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____006_1.name = "物体信息.006"
    _____006_1.transform_space = 'ORIGINAL'
    # As Instance
    _____006_1.inputs[1].default_value = False

    # Node 自身物体.001
    _____001_5 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSelfObject")
    _____001_5.name = "自身物体.001"

    # Node 物体信息.007
    _____007_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____007_1.name = "物体信息.007"
    _____007_1.transform_space = 'ORIGINAL'
    # As Instance
    _____007_1.inputs[1].default_value = False

    # Node 投影点
    ____3 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeProjectPoint")
    ____3.name = "投影点"

    # Node 合并变换.001
    _____001_6 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeCombineTransform")
    _____001_6.name = "合并变换.001"
    _____001_6.inputs[0].hide = True
    # Translation
    _____001_6.inputs[0].default_value = (0.0, 0.0, 0.0)

    # Node 矩阵相乘.003
    _____003_5 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeMatrixMultiply")
    _____003_5.name = "矩阵相乘.003"

    # Node 旋转矢量
    _____6 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeRotateVector")
    _____6.name = "旋转矢量"

    # Node 物体信息.002
    _____002_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____002_3.name = "物体信息.002"
    _____002_3.transform_space = 'RELATIVE'
    # As Instance
    _____002_3.inputs[1].default_value = False

    # Node 位置.010
    ___010_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputPosition")
    ___010_3.name = "位置.010"

    # Node 光线投射
    _____7 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRaycast")
    _____7.name = "光线投射"
    _____7.data_type = 'FLOAT'
    # Attribute
    _____7.inputs[1].default_value = 0.0
    # Interpolation
    _____7.inputs[2].default_value = 'Interpolated'
    # Ray Length
    _____7.inputs[5].default_value = 1024.0

    # Node 矢量运算.022
    _____022 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____022.name = "矢量运算.022"
    _____022.hide = True
    _____022.operation = 'SUBTRACT'

    # Node 转接点.054
    ____054 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____054.name = "转接点.054"
    ____054.socket_idname = "NodeSocketVector"
    # Node 布尔运算
    _____8 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeBooleanMath")
    _____8.name = "布尔运算"
    _____8.operation = 'NOT'

    # Node 运算.086
    ___086 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___086.name = "运算.086"
    ___086.hide = True
    ___086.operation = 'MULTIPLY'
    ___086.use_clamp = False

    # Node Camera Info
    camera_info = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeCameraInfo")
    camera_info.name = "Camera Info"

    # Node 删除几何体.008
    ______008_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDeleteGeometry")
    ______008_1.name = "删除几何体.008"
    ______008_1.domain = 'POINT'
    ______008_1.mode = 'ALL'

    # Node 物体信息.008
    _____008_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____008_2.name = "物体信息.008"
    _____008_2.transform_space = 'ORIGINAL'
    # As Instance
    _____008_2.inputs[1].default_value = False

    # Node 变换点.001
    ____001_4 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeTransformPoint")
    ____001_4.name = "变换点.001"

    # Node 逆矩阵
    ____4 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeInvertMatrix")
    ____4.name = "逆矩阵"

    # Node 投影点.001
    ____001_5 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeProjectPoint")
    ____001_5.name = "投影点.001"

    # Node 矢量运算.001
    _____001_7 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____001_7.name = "矢量运算.001"
    _____001_7.hide = True
    _____001_7.operation = 'ABSOLUTE'

    # Node 自身物体.002
    _____002_4 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSelfObject")
    _____002_4.name = "自身物体.002"

    # Node 物体信息.009
    _____009_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____009_1.name = "物体信息.009"
    _____009_1.transform_space = 'ORIGINAL'
    # As Instance
    _____009_1.inputs[1].default_value = False

    # Node 投影点.002
    ____002_2 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeProjectPoint")
    ____002_2.name = "投影点.002"

    # Node 位置.011
    ___011_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputPosition")
    ___011_1.name = "位置.011"

    # Node 组输入
    ____5 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____5.name = "组输入"
    ____5.outputs[0].hide = True
    ____5.outputs[1].hide = True
    ____5.outputs[3].hide = True
    ____5.outputs[4].hide = True
    ____5.outputs[5].hide = True
    ____5.outputs[6].hide = True
    ____5.outputs[7].hide = True
    ____5.outputs[8].hide = True
    ____5.outputs[9].hide = True
    ____5.outputs[10].hide = True
    ____5.outputs[11].hide = True
    ____5.outputs[12].hide = True
    ____5.outputs[13].hide = True
    ____5.outputs[14].hide = True
    ____5.outputs[15].hide = True
    ____5.outputs[16].hide = True
    ____5.outputs[17].hide = True
    ____5.outputs[18].hide = True
    ____5.outputs[19].hide = True
    ____5.outputs[20].hide = True
    ____5.outputs[21].hide = True
    ____5.outputs[22].hide = True
    ____5.outputs[23].hide = True
    ____5.outputs[24].hide = True
    ____5.outputs[25].hide = True
    ____5.outputs[26].hide = True
    ____5.outputs[27].hide = True
    ____5.outputs[28].hide = True
    ____5.outputs[29].hide = True
    ____5.outputs[30].hide = True
    ____5.outputs[31].hide = True
    ____5.outputs[32].hide = True
    ____5.outputs[33].hide = True
    ____5.outputs[34].hide = True
    ____5.outputs[35].hide = True
    ____5.outputs[36].hide = True
    ____5.outputs[37].hide = True
    ____5.outputs[38].hide = True
    ____5.outputs[39].hide = True
    ____5.outputs[40].hide = True

    # Node 切换.012
    ___012_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___012_2.name = "切换.012"
    ___012_2.input_type = 'GEOMETRY'

    # Node 组输出
    ____6 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupOutput")
    ____6.name = "组输出"
    ____6.is_active_output = True

    # Node 矢量运算.023
    _____023 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____023.name = "矢量运算.023"
    _____023.operation = 'SCALE'

    # Node input_point_radius.026
    input_point_radius_026 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_026.name = "input_point_radius.026"
    input_point_radius_026.outputs[0].hide = True
    input_point_radius_026.outputs[1].hide = True
    input_point_radius_026.outputs[2].hide = True
    input_point_radius_026.outputs[3].hide = True
    input_point_radius_026.outputs[4].hide = True
    input_point_radius_026.outputs[5].hide = True
    input_point_radius_026.outputs[6].hide = True
    input_point_radius_026.outputs[7].hide = True
    input_point_radius_026.outputs[8].hide = True
    input_point_radius_026.outputs[9].hide = True
    input_point_radius_026.outputs[10].hide = True
    input_point_radius_026.outputs[11].hide = True
    input_point_radius_026.outputs[12].hide = True
    input_point_radius_026.outputs[13].hide = True
    input_point_radius_026.outputs[14].hide = True
    input_point_radius_026.outputs[15].hide = True
    input_point_radius_026.outputs[16].hide = True
    input_point_radius_026.outputs[17].hide = True
    input_point_radius_026.outputs[18].hide = True
    input_point_radius_026.outputs[19].hide = True
    input_point_radius_026.outputs[20].hide = True
    input_point_radius_026.outputs[21].hide = True
    input_point_radius_026.outputs[22].hide = True
    input_point_radius_026.outputs[24].hide = True
    input_point_radius_026.outputs[25].hide = True
    input_point_radius_026.outputs[26].hide = True
    input_point_radius_026.outputs[27].hide = True
    input_point_radius_026.outputs[28].hide = True
    input_point_radius_026.outputs[29].hide = True
    input_point_radius_026.outputs[30].hide = True
    input_point_radius_026.outputs[31].hide = True
    input_point_radius_026.outputs[32].hide = True
    input_point_radius_026.outputs[33].hide = True
    input_point_radius_026.outputs[34].hide = True
    input_point_radius_026.outputs[35].hide = True
    input_point_radius_026.outputs[36].hide = True
    input_point_radius_026.outputs[37].hide = True
    input_point_radius_026.outputs[38].hide = True
    input_point_radius_026.outputs[39].hide = True
    input_point_radius_026.outputs[40].hide = True

    # Node 菜单切换.006
    _____006_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____006_2.name = "菜单切换.006"
    _____006_2.active_index = 2
    _____006_2.data_type = 'GEOMETRY'
    _____006_2.enum_items.clear()
    _____006_2.enum_items.new("Cube")
    _____006_2.enum_items[0].description = ""
    _____006_2.enum_items.new("IcoSphere")
    _____006_2.enum_items[1].description = ""
    _____006_2.enum_items.new("DualIcoSphere")
    _____006_2.enum_items[2].description = ""

    # Node Mesh to Points.003
    mesh_to_points_003 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMeshToPoints")
    mesh_to_points_003.name = "Mesh to Points.003"
    mesh_to_points_003.mode = 'VERTICES'
    # Selection
    mesh_to_points_003.inputs[1].default_value = True
    # Position
    mesh_to_points_003.inputs[2].default_value = (0.0, 0.0, 0.0)

    # Node 位置.004
    ___004_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputPosition")
    ___004_2.name = "位置.004"

    # Node 删除已命名属性
    _______ = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRemoveAttribute")
    _______.name = "删除已命名属性"
    # Pattern Mode
    _______.inputs[1].default_value = 'Wildcard'
    # Name
    _______.inputs[2].default_value = "f_*"

    # Node 转接点.011
    ____011_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____011_1.name = "转接点.011"
    ____011_1.socket_idname = "NodeSocketVector"
    # Node input_point_radius.027
    input_point_radius_027 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_027.name = "input_point_radius.027"
    input_point_radius_027.outputs[0].hide = True
    input_point_radius_027.outputs[1].hide = True
    input_point_radius_027.outputs[2].hide = True
    input_point_radius_027.outputs[3].hide = True
    input_point_radius_027.outputs[4].hide = True
    input_point_radius_027.outputs[5].hide = True
    input_point_radius_027.outputs[6].hide = True
    input_point_radius_027.outputs[7].hide = True
    input_point_radius_027.outputs[8].hide = True
    input_point_radius_027.outputs[9].hide = True
    input_point_radius_027.outputs[10].hide = True
    input_point_radius_027.outputs[11].hide = True
    input_point_radius_027.outputs[12].hide = True
    input_point_radius_027.outputs[13].hide = True
    input_point_radius_027.outputs[14].hide = True
    input_point_radius_027.outputs[15].hide = True
    input_point_radius_027.outputs[16].hide = True
    input_point_radius_027.outputs[17].hide = True
    input_point_radius_027.outputs[18].hide = True
    input_point_radius_027.outputs[19].hide = True
    input_point_radius_027.outputs[20].hide = True
    input_point_radius_027.outputs[21].hide = True
    input_point_radius_027.outputs[22].hide = True
    input_point_radius_027.outputs[23].hide = True
    input_point_radius_027.outputs[24].hide = True
    input_point_radius_027.outputs[25].hide = True
    input_point_radius_027.outputs[26].hide = True
    input_point_radius_027.outputs[27].hide = True
    input_point_radius_027.outputs[28].hide = True
    input_point_radius_027.outputs[29].hide = True
    input_point_radius_027.outputs[30].hide = True
    input_point_radius_027.outputs[31].hide = True
    input_point_radius_027.outputs[32].hide = True
    input_point_radius_027.outputs[34].hide = True
    input_point_radius_027.outputs[35].hide = True
    input_point_radius_027.outputs[36].hide = True
    input_point_radius_027.outputs[37].hide = True
    input_point_radius_027.outputs[38].hide = True
    input_point_radius_027.outputs[39].hide = True
    input_point_radius_027.outputs[40].hide = True

    # Node 转接点.028
    ____028 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____028.name = "转接点.028"
    ____028.socket_idname = "NodeSocketGeometry"
    # Node 已命名属性.029
    ______029 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______029.name = "已命名属性.029"
    ______029.data_type = 'FLOAT'
    # Name
    ______029.inputs[0].default_value = "motion_0"

    # Node 已命名属性.030
    ______030 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______030.name = "已命名属性.030"
    ______030.data_type = 'FLOAT'
    # Name
    ______030.inputs[0].default_value = "motion_1"

    # Node 已命名属性.047
    ______047 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______047.name = "已命名属性.047"
    ______047.data_type = 'FLOAT'
    # Name
    ______047.inputs[0].default_value = "motion_2"

    # Node 合并 XYZ.006
    ___xyz_006 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeCombineXYZ")
    ___xyz_006.name = "合并 XYZ.006"

    # Node 矢量运算.032
    _____032 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____032.name = "矢量运算.032"
    _____032.operation = 'ADD'
    # Vector_001
    _____032.inputs[1].default_value = (0.5, 0.5, 0.5)

    # Node 矢量运算.034
    _____034 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____034.name = "矢量运算.034"
    _____034.operation = 'NORMALIZE'

    # Node input_point_radius.028
    input_point_radius_028 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_028.name = "input_point_radius.028"
    input_point_radius_028.outputs[0].hide = True
    input_point_radius_028.outputs[1].hide = True
    input_point_radius_028.outputs[2].hide = True
    input_point_radius_028.outputs[3].hide = True
    input_point_radius_028.outputs[4].hide = True
    input_point_radius_028.outputs[5].hide = True
    input_point_radius_028.outputs[6].hide = True
    input_point_radius_028.outputs[7].hide = True
    input_point_radius_028.outputs[8].hide = True
    input_point_radius_028.outputs[9].hide = True
    input_point_radius_028.outputs[10].hide = True
    input_point_radius_028.outputs[11].hide = True
    input_point_radius_028.outputs[12].hide = True
    input_point_radius_028.outputs[13].hide = True
    input_point_radius_028.outputs[14].hide = True
    input_point_radius_028.outputs[15].hide = True
    input_point_radius_028.outputs[16].hide = True
    input_point_radius_028.outputs[17].hide = True
    input_point_radius_028.outputs[18].hide = True
    input_point_radius_028.outputs[19].hide = True
    input_point_radius_028.outputs[20].hide = True
    input_point_radius_028.outputs[21].hide = True
    input_point_radius_028.outputs[22].hide = True
    input_point_radius_028.outputs[23].hide = True
    input_point_radius_028.outputs[24].hide = True
    input_point_radius_028.outputs[25].hide = True
    input_point_radius_028.outputs[26].hide = True
    input_point_radius_028.outputs[27].hide = True
    input_point_radius_028.outputs[28].hide = True
    input_point_radius_028.outputs[29].hide = True
    input_point_radius_028.outputs[30].hide = True
    input_point_radius_028.outputs[31].hide = True
    input_point_radius_028.outputs[32].hide = True
    input_point_radius_028.outputs[33].hide = True
    input_point_radius_028.outputs[34].hide = True
    input_point_radius_028.outputs[35].hide = True
    input_point_radius_028.outputs[36].hide = True
    input_point_radius_028.outputs[37].hide = True
    input_point_radius_028.outputs[40].hide = True

    # Node 切换.013
    ___013_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___013_2.name = "切换.013"
    ___013_2.input_type = 'VECTOR'

    # Node 切换.014
    ___014_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___014_2.name = "切换.014"
    ___014_2.input_type = 'VECTOR'

    # Node 矢量运算.035
    _____035 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____035.name = "矢量运算.035"
    _____035.operation = 'LENGTH'

    # Node 设置材质
    _____9 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSetMaterial")
    _____9.name = "设置材质"
    # Selection
    _____9.inputs[1].default_value = True
    if "UGRP_Shader_G" in bpy.data.materials:
        _____9.inputs[2].default_value = bpy.data.materials["UGRP_Shader_G"]

    # Node 切换.017
    ___017_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___017_2.name = "切换.017"
    ___017_2.input_type = 'GEOMETRY'

    # Node 矢量运算.036
    _____036 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____036.name = "矢量运算.036"
    _____036.operation = 'LENGTH'

    # Node 运算.028
    ___028 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___028.name = "运算.028"
    ___028.operation = 'LESS_THAN'
    ___028.use_clamp = False
    # Value_001
    ___028.inputs[1].default_value = 0.10000000149011612

    # Node 元素排序
    _____10 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSortElements")
    _____10.name = "元素排序"
    _____10.domain = 'POINT'
    # Selection
    _____10.inputs[1].default_value = True
    # Group ID
    _____10.inputs[2].default_value = 0

    # Node 物体信息.012
    _____012_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____012_1.name = "物体信息.012"
    _____012_1.transform_space = 'RELATIVE'
    # As Instance
    _____012_1.inputs[1].default_value = False

    # Node 位置.005
    ___005_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputPosition")
    ___005_1.name = "位置.005"

    # Node 活动摄像机.001
    ______001_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputActiveCamera")
    ______001_1.name = "活动摄像机.001"

    # Node 矢量运算.037
    _____037 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____037.name = "矢量运算.037"
    _____037.operation = 'DISTANCE'

    # Node 运算.001
    ___001_2 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___001_2.name = "运算.001"
    ___001_2.operation = 'MULTIPLY'
    ___001_2.use_clamp = False
    # Value_001
    ___001_2.inputs[1].default_value = -1.0

    # Node 分离 XYZ.002
    ___xyz_002_1 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeSeparateXYZ")
    ___xyz_002_1.name = "分离 XYZ.002"

    # Node 烘焙.002
    ___002_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeBake")
    ___002_2.name = "烘焙.002"
    ___002_2.active_index = 0
    ___002_2.bake_items.clear()
    ___002_2.bake_items.new('GEOMETRY', "几何数据")
    ___002_2.bake_items[0].attribute_domain = 'POINT'

    # Node 删除几何体.010
    ______010_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeDeleteGeometry")
    ______010_1.name = "删除几何体.010"
    ______010_1.domain = 'POINT'
    ______010_1.mode = 'ALL'

    # Node 已命名属性.001
    ______001_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______001_2.name = "已命名属性.001"
    ______001_2.data_type = 'FLOAT'
    # Name
    ______001_2.inputs[0].default_value = "t_scale"

    # Node 运算.060
    ___060 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___060.name = "运算.060"
    ___060.operation = 'EXPONENT'
    ___060.use_clamp = False

    # Node 运算.087
    ___087 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___087.name = "运算.087"
    ___087.mute = True
    ___087.operation = 'POWER'
    ___087.use_clamp = False
    # Value_001
    ___087.inputs[1].default_value = 2.0

    # Node 运算.088
    ___088 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___088.name = "运算.088"
    ___088.operation = 'MULTIPLY'
    ___088.use_clamp = False
    # Value_001
    ___088.inputs[1].default_value = 1.0

    # Node 运算.094
    ___094 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___094.name = "运算.094"
    ___094.operation = 'DIVIDE'
    ___094.use_clamp = False
    # Value
    ___094.inputs[0].default_value = 1.0

    # Node 运算.095
    ___095 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___095.name = "运算.095"
    ___095.mute = True
    ___095.operation = 'EXPONENT'
    ___095.use_clamp = False

    # Node 曲线圆环
    _____11 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeCurvePrimitiveCircle")
    _____11.name = "曲线圆环"
    _____11.mode = 'RADIUS'
    # Radius
    _____11.inputs[4].default_value = 1.0

    # Node 填充曲线.004
    _____004_4 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeFillCurve")
    _____004_4.name = "填充曲线.004"
    # Group ID
    _____004_4.inputs[1].default_value = 0
    # Mode
    _____004_4.inputs[2].default_value = 'N-gons'

    # Node 切换.018
    ___018_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSwitch")
    ___018_2.name = "切换.018"
    ___018_2.input_type = 'FLOAT'
    # False
    ___018_2.inputs[1].default_value = 9.999999747378752e-06

    # Node 组输入.004
    ____004_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____004_1.name = "组输入.004"
    ____004_1.outputs[0].hide = True
    ____004_1.outputs[1].hide = True
    ____004_1.outputs[2].hide = True
    ____004_1.outputs[3].hide = True
    ____004_1.outputs[4].hide = True
    ____004_1.outputs[5].hide = True
    ____004_1.outputs[6].hide = True
    ____004_1.outputs[7].hide = True
    ____004_1.outputs[8].hide = True
    ____004_1.outputs[9].hide = True
    ____004_1.outputs[10].hide = True
    ____004_1.outputs[11].hide = True
    ____004_1.outputs[12].hide = True
    ____004_1.outputs[13].hide = True
    ____004_1.outputs[14].hide = True
    ____004_1.outputs[15].hide = True
    ____004_1.outputs[16].hide = True
    ____004_1.outputs[17].hide = True
    ____004_1.outputs[18].hide = True
    ____004_1.outputs[19].hide = True
    ____004_1.outputs[20].hide = True
    ____004_1.outputs[21].hide = True
    ____004_1.outputs[23].hide = True
    ____004_1.outputs[25].hide = True
    ____004_1.outputs[26].hide = True
    ____004_1.outputs[27].hide = True
    ____004_1.outputs[28].hide = True
    ____004_1.outputs[29].hide = True
    ____004_1.outputs[30].hide = True
    ____004_1.outputs[31].hide = True
    ____004_1.outputs[32].hide = True
    ____004_1.outputs[33].hide = True
    ____004_1.outputs[34].hide = True
    ____004_1.outputs[35].hide = True
    ____004_1.outputs[36].hide = True
    ____004_1.outputs[37].hide = True
    ____004_1.outputs[38].hide = True
    ____004_1.outputs[39].hide = True
    ____004_1.outputs[40].hide = True

    # Node 菜单切换.007
    _____007_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____007_2.name = "菜单切换.007"
    _____007_2.active_index = 1
    _____007_2.data_type = 'GEOMETRY'
    _____007_2.enum_items.clear()
    _____007_2.enum_items.new("3DGS")
    _____007_2.enum_items[0].description = ""
    _____007_2.enum_items.new("2DGS")
    _____007_2.enum_items[1].description = ""

    # Node 编号切换
    _____12 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeIndexSwitch")
    _____12.name = "编号切换"
    _____12.data_type = 'VECTOR'
    _____12.index_switch_items.clear()
    _____12.index_switch_items.new()
    _____12.index_switch_items.new()
    _____12.index_switch_items.new()
    _____12.index_switch_items.new()

    # Node 组输入.010
    ____010_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____010_1.name = "组输入.010"
    ____010_1.outputs[0].hide = True
    ____010_1.outputs[1].hide = True
    ____010_1.outputs[2].hide = True
    ____010_1.outputs[3].hide = True
    ____010_1.outputs[4].hide = True
    ____010_1.outputs[5].hide = True
    ____010_1.outputs[6].hide = True
    ____010_1.outputs[7].hide = True
    ____010_1.outputs[8].hide = True
    ____010_1.outputs[9].hide = True
    ____010_1.outputs[10].hide = True
    ____010_1.outputs[11].hide = True
    ____010_1.outputs[12].hide = True
    ____010_1.outputs[13].hide = True
    ____010_1.outputs[14].hide = True
    ____010_1.outputs[15].hide = True
    ____010_1.outputs[16].hide = True
    ____010_1.outputs[17].hide = True
    ____010_1.outputs[18].hide = True
    ____010_1.outputs[19].hide = True
    ____010_1.outputs[20].hide = True
    ____010_1.outputs[21].hide = True
    ____010_1.outputs[22].hide = True
    ____010_1.outputs[23].hide = True
    ____010_1.outputs[24].hide = True
    ____010_1.outputs[25].hide = True
    ____010_1.outputs[26].hide = True
    ____010_1.outputs[27].hide = True
    ____010_1.outputs[28].hide = True
    ____010_1.outputs[29].hide = True
    ____010_1.outputs[30].hide = True
    ____010_1.outputs[31].hide = True
    ____010_1.outputs[32].hide = True
    ____010_1.outputs[33].hide = True
    ____010_1.outputs[34].hide = True
    ____010_1.outputs[36].hide = True
    ____010_1.outputs[37].hide = True
    ____010_1.outputs[38].hide = True
    ____010_1.outputs[39].hide = True
    ____010_1.outputs[40].hide = True

    # Node 转接点.026
    ____026 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____026.name = "转接点.026"
    ____026.socket_idname = "NodeSocketFloat"
    # Node 分离 XYZ.003
    ___xyz_003_1 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeSeparateXYZ")
    ___xyz_003_1.name = "分离 XYZ.003"

    # Node 转接点.029
    ____029 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____029.name = "转接点.029"
    ____029.socket_idname = "NodeSocketVectorXYZ"
    # Node 群组.020
    ___020_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeGroup")
    ___020_1.name = "群组.020"
    ___020_1.node_tree = bpy.data.node_groups[node_tree_names[sh_g_1_node_group]]

    # Node 自身物体.004
    _____004_5 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSelfObject")
    _____004_5.name = "自身物体.004"

    # Node 物体信息.013
    _____013_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____013_1.name = "物体信息.013"
    _____013_1.transform_space = 'ORIGINAL'
    # As Instance
    _____013_1.inputs[1].default_value = False

    # Node 转接点.042
    ____042 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____042.name = "转接点.042"
    ____042.socket_idname = "NodeSocketGeometry"
    # Node 组输入.016
    ____016 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____016.name = "组输入.016"
    ____016.outputs[0].hide = True
    ____016.outputs[1].hide = True
    ____016.outputs[2].hide = True
    ____016.outputs[3].hide = True
    ____016.outputs[4].hide = True
    ____016.outputs[5].hide = True
    ____016.outputs[6].hide = True
    ____016.outputs[7].hide = True
    ____016.outputs[8].hide = True
    ____016.outputs[9].hide = True
    ____016.outputs[10].hide = True
    ____016.outputs[11].hide = True
    ____016.outputs[12].hide = True
    ____016.outputs[13].hide = True
    ____016.outputs[14].hide = True
    ____016.outputs[15].hide = True
    ____016.outputs[16].hide = True
    ____016.outputs[17].hide = True
    ____016.outputs[18].hide = True
    ____016.outputs[19].hide = True
    ____016.outputs[20].hide = True
    ____016.outputs[21].hide = True
    ____016.outputs[22].hide = True
    ____016.outputs[23].hide = True
    ____016.outputs[24].hide = True
    ____016.outputs[25].hide = True
    ____016.outputs[26].hide = True
    ____016.outputs[27].hide = True
    ____016.outputs[28].hide = True
    ____016.outputs[29].hide = True
    ____016.outputs[30].hide = True
    ____016.outputs[31].hide = True
    ____016.outputs[32].hide = True
    ____016.outputs[33].hide = True
    ____016.outputs[34].hide = True
    ____016.outputs[35].hide = True
    ____016.outputs[37].hide = True
    ____016.outputs[38].hide = True
    ____016.outputs[39].hide = True
    ____016.outputs[40].hide = True

    # Node 重复输入.001
    _____001_8 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRepeatInput")
    _____001_8.name = "重复输入.001"
    # Node 重复输出.001
    _____001_9 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeRepeatOutput")
    _____001_9.name = "重复输出.001"
    _____001_9.active_index = 0
    _____001_9.inspection_index = 0
    _____001_9.repeat_items.clear()
    # Create item "几何数据"
    _____001_9.repeat_items.new('VECTOR', "几何数据")

    # Node 整数运算.010
    _____010_1 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____010_1.name = "整数运算.010"
    _____010_1.operation = 'SUBTRACT'

    # Node 整数运算.011
    _____011_1 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____011_1.name = "整数运算.011"
    _____011_1.operation = 'ADD'
    # Value_001
    _____011_1.inputs[1].default_value = 1

    # Node 矢量运算.084
    _____084 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____084.name = "矢量运算.084"
    _____084.hide = True
    _____084.operation = 'ADD'

    # Node 整数运算.012
    _____012_2 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeIntegerMath")
    _____012_2.name = "整数运算.012"
    _____012_2.operation = 'ADD'

    # Node 运算.089
    ___089 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___089.name = "运算.089"
    ___089.hide = True
    ___089.operation = 'LESS_THAN'
    ___089.use_clamp = False

    # Node input_point_radius.006
    input_point_radius_006 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_006.name = "input_point_radius.006"
    input_point_radius_006.outputs[0].hide = True
    input_point_radius_006.outputs[1].hide = True
    input_point_radius_006.outputs[2].hide = True
    input_point_radius_006.outputs[3].hide = True
    input_point_radius_006.outputs[4].hide = True
    input_point_radius_006.outputs[5].hide = True
    input_point_radius_006.outputs[6].hide = True
    input_point_radius_006.outputs[7].hide = True
    input_point_radius_006.outputs[8].hide = True
    input_point_radius_006.outputs[9].hide = True
    input_point_radius_006.outputs[10].hide = True
    input_point_radius_006.outputs[11].hide = True
    input_point_radius_006.outputs[12].hide = True
    input_point_radius_006.outputs[13].hide = True
    input_point_radius_006.outputs[14].hide = True
    input_point_radius_006.outputs[15].hide = True
    input_point_radius_006.outputs[16].hide = True
    input_point_radius_006.outputs[17].hide = True
    input_point_radius_006.outputs[18].hide = True
    input_point_radius_006.outputs[19].hide = True
    input_point_radius_006.outputs[20].hide = True
    input_point_radius_006.outputs[21].hide = True
    input_point_radius_006.outputs[22].hide = True
    input_point_radius_006.outputs[23].hide = True
    input_point_radius_006.outputs[24].hide = True
    input_point_radius_006.outputs[25].hide = True
    input_point_radius_006.outputs[27].hide = True
    input_point_radius_006.outputs[28].hide = True
    input_point_radius_006.outputs[29].hide = True
    input_point_radius_006.outputs[30].hide = True
    input_point_radius_006.outputs[31].hide = True
    input_point_radius_006.outputs[32].hide = True
    input_point_radius_006.outputs[33].hide = True
    input_point_radius_006.outputs[34].hide = True
    input_point_radius_006.outputs[35].hide = True
    input_point_radius_006.outputs[36].hide = True
    input_point_radius_006.outputs[37].hide = True
    input_point_radius_006.outputs[38].hide = True
    input_point_radius_006.outputs[39].hide = True
    input_point_radius_006.outputs[40].hide = True

    # Node 转接点.013
    ____013_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____013_1.name = "转接点.013"
    ____013_1.socket_idname = "NodeSocketRotation"
    # Node 变换几何体.001
    ______001_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeTransform")
    ______001_3.name = "变换几何体.001"
    ______001_3.hide = True
    # Mode
    ______001_3.inputs[1].default_value = 'Components'
    # Translation
    ______001_3.inputs[2].default_value = (0.0, 0.0, 0.0)
    # Rotation
    ______001_3.inputs[3].default_value = (0.0, 0.0, 0.0)
    # Scale
    ______001_3.inputs[4].default_value = (1.4140000343322754, 1.4140000343322754, 1.4140000343322754)

    # Node 运算.007
    ___007_2 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___007_2.name = "运算.007"
    ___007_2.operation = 'GREATER_THAN'
    ___007_2.use_clamp = False
    # Value_001
    ___007_2.inputs[1].default_value = 1.100000023841858

    # Node 分离 XYZ.004
    ___xyz_004_1 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeSeparateXYZ")
    ___xyz_004_1.name = "分离 XYZ.004"
    ___xyz_004_1.hide = True

    # Node 运算.019
    ___019_1 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___019_1.name = "运算.019"
    ___019_1.operation = 'GREATER_THAN'
    ___019_1.use_clamp = False
    # Value_001
    ___019_1.inputs[1].default_value = 1.2000000476837158

    # Node 运算.030
    ___030 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___030.name = "运算.030"
    ___030.operation = 'GREATER_THAN'
    ___030.use_clamp = False
    # Value_001
    ___030.inputs[1].default_value = 1.0

    # Node 布尔运算.004
    _____004_6 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeBooleanMath")
    _____004_6.name = "布尔运算.004"
    _____004_6.hide = True
    _____004_6.operation = 'OR'

    # Node 布尔运算.005
    _____005_2 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeBooleanMath")
    _____005_2.name = "布尔运算.005"
    _____005_2.hide = True
    _____005_2.operation = 'OR'

    # Node 存储已命名属性.010
    ________010 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeStoreNamedAttribute")
    ________010.name = "存储已命名属性.010"
    ________010.data_type = 'INT'
    ________010.domain = 'POINT'
    # Selection
    ________010.inputs[1].default_value = True
    # Name
    ________010.inputs[2].default_value = "Mode"

    # Node 活动摄像机.003
    ______003_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputActiveCamera")
    ______003_2.name = "活动摄像机.003"

    # Node 活动摄像机.004
    ______004_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputActiveCamera")
    ______004_1.name = "活动摄像机.004"

    # Node 自身物体.005
    _____005_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSelfObject")
    _____005_3.name = "自身物体.005"

    # Node 物体信息.014
    _____014_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____014_1.name = "物体信息.014"
    _____014_1.transform_space = 'ORIGINAL'
    # As Instance
    _____014_1.inputs[1].default_value = False

    # Node 转接点.014
    ____014_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____014_1.name = "转接点.014"
    ____014_1.socket_idname = "NodeSocketVectorXYZ"
    # Node 变换方向
    _____13 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeTransformDirection")
    _____13.name = "变换方向"

    # Node 转接点.015
    ____015 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____015.name = "转接点.015"
    ____015.socket_idname = "NodeSocketVector"
    # Node 矢量运算.085
    _____085 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____085.name = "矢量运算.085"
    _____085.hide = True
    _____085.operation = 'MINIMUM'
    # Vector_001
    _____085.inputs[1].default_value = (1.0, 1.0, 1.0)

    # Node 矢量运算.086
    _____086 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____086.name = "矢量运算.086"
    _____086.hide = True
    _____086.operation = 'MAXIMUM'
    # Vector_001
    _____086.inputs[1].default_value = (0.0, 0.0, 0.0)

    # Node 转接点.016
    ____016_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____016_1.name = "转接点.016"
    ____016_1.socket_idname = "NodeSocketVector"
    # Node 已命名属性.055
    ______055 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______055.name = "已命名属性.055"
    ______055.data_type = 'FLOAT_VECTOR'
    # Name
    ______055.inputs[0].default_value = "Pre_Normal"

    # Node 矢量运算.033
    _____033 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____033.name = "矢量运算.033"
    _____033.operation = 'ADD'
    # Vector_001
    _____033.inputs[1].default_value = (1.0, 1.0, 1.0)

    # Node 矢量运算.039
    _____039 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____039.name = "矢量运算.039"
    _____039.operation = 'MULTIPLY'
    # Vector_001
    _____039.inputs[1].default_value = (0.5, 0.5, 0.5)

    # Node 矢量运算.027
    _____027 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____027.name = "矢量运算.027"
    _____027.operation = 'FACEFORWARD'

    # Node 自身物体.008
    _____008_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeSelfObject")
    _____008_3.name = "自身物体.008"

    # Node 物体信息.018
    _____018_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____018_1.name = "物体信息.018"
    _____018_1.transform_space = 'ORIGINAL'
    # As Instance
    _____018_1.inputs[1].default_value = False

    # Node 活动摄像机.007
    ______007_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputActiveCamera")
    ______007_2.name = "活动摄像机.007"

    # Node 物体信息.019
    _____019_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeObjectInfo")
    _____019_1.name = "物体信息.019"
    _____019_1.transform_space = 'ORIGINAL'
    # As Instance
    _____019_1.inputs[1].default_value = False

    # Node 矢量运算.040
    _____040 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____040.name = "矢量运算.040"
    _____040.operation = 'SUBTRACT'

    # Node 位置.006
    ___006_1 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputPosition")
    ___006_1.name = "位置.006"

    # Node 投影点.006
    ____006_2 = ugrs_mainnodetree_v1_0_1.nodes.new("FunctionNodeProjectPoint")
    ____006_2.name = "投影点.006"

    # Node 菜单切换.008
    _____008_4 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____008_4.name = "菜单切换.008"
    _____008_4.active_index = 0
    _____008_4.data_type = 'VECTOR'
    _____008_4.enum_items.clear()
    _____008_4.enum_items.new("Off")
    _____008_4.enum_items[0].description = ""
    _____008_4.enum_items.new("On")
    _____008_4.enum_items[1].description = ""

    # Node 组输入.017
    ____017_1 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    ____017_1.name = "组输入.017"
    ____017_1.outputs[1].hide = True
    ____017_1.outputs[2].hide = True
    ____017_1.outputs[3].hide = True
    ____017_1.outputs[4].hide = True
    ____017_1.outputs[5].hide = True
    ____017_1.outputs[6].hide = True
    ____017_1.outputs[7].hide = True
    ____017_1.outputs[8].hide = True
    ____017_1.outputs[9].hide = True
    ____017_1.outputs[10].hide = True
    ____017_1.outputs[11].hide = True
    ____017_1.outputs[12].hide = True
    ____017_1.outputs[13].hide = True
    ____017_1.outputs[14].hide = True
    ____017_1.outputs[15].hide = True
    ____017_1.outputs[16].hide = True
    ____017_1.outputs[17].hide = True
    ____017_1.outputs[18].hide = True
    ____017_1.outputs[19].hide = True
    ____017_1.outputs[20].hide = True
    ____017_1.outputs[21].hide = True
    ____017_1.outputs[22].hide = True
    ____017_1.outputs[23].hide = True
    ____017_1.outputs[24].hide = True
    ____017_1.outputs[25].hide = True
    ____017_1.outputs[26].hide = True
    ____017_1.outputs[27].hide = True
    ____017_1.outputs[28].hide = True
    ____017_1.outputs[29].hide = True
    ____017_1.outputs[30].hide = True
    ____017_1.outputs[31].hide = True
    ____017_1.outputs[32].hide = True
    ____017_1.outputs[33].hide = True
    ____017_1.outputs[34].hide = True
    ____017_1.outputs[35].hide = True
    ____017_1.outputs[36].hide = True
    ____017_1.outputs[37].hide = True
    ____017_1.outputs[38].hide = True
    ____017_1.outputs[39].hide = True
    ____017_1.outputs[40].hide = True

    # Node 转接点.044
    ____044 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____044.name = "转接点.044"
    ____044.socket_idname = "NodeSocketFloat"
    # Node 运算.100
    ___100 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___100.name = "运算.100"
    ___100.hide = True
    ___100.operation = 'ADD'
    ___100.use_clamp = False

    # Node 菜单切换.009
    _____009_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____009_2.name = "菜单切换.009"
    _____009_2.hide = True
    _____009_2.active_index = 1
    _____009_2.data_type = 'FLOAT'
    _____009_2.enum_items.clear()
    _____009_2.enum_items.new("Off")
    _____009_2.enum_items[0].description = ""
    _____009_2.enum_items.new("On")
    _____009_2.enum_items[1].description = ""

    # Node 转接点.045
    ____045 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    ____045.name = "转接点.045"
    ____045.socket_idname = "NodeSocketGeometry"
    # Node 菜单切换.010
    _____010_2 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeMenuSwitch")
    _____010_2.name = "菜单切换.010"
    _____010_2.active_index = 1
    _____010_2.data_type = 'FLOAT'
    _____010_2.enum_items.clear()
    _____010_2.enum_items.new("NDC")
    _____010_2.enum_items[0].description = ""
    _____010_2.enum_items.new("WORD")
    _____010_2.enum_items[1].description = ""

    # Node input_point_radius.029
    input_point_radius_029 = ugrs_mainnodetree_v1_0_1.nodes.new("NodeGroupInput")
    input_point_radius_029.name = "input_point_radius.029"
    input_point_radius_029.outputs[0].hide = True
    input_point_radius_029.outputs[1].hide = True
    input_point_radius_029.outputs[2].hide = True
    input_point_radius_029.outputs[3].hide = True
    input_point_radius_029.outputs[4].hide = True
    input_point_radius_029.outputs[5].hide = True
    input_point_radius_029.outputs[6].hide = True
    input_point_radius_029.outputs[7].hide = True
    input_point_radius_029.outputs[8].hide = True
    input_point_radius_029.outputs[9].hide = True
    input_point_radius_029.outputs[10].hide = True
    input_point_radius_029.outputs[11].hide = True
    input_point_radius_029.outputs[12].hide = True
    input_point_radius_029.outputs[13].hide = True
    input_point_radius_029.outputs[14].hide = True
    input_point_radius_029.outputs[15].hide = True
    input_point_radius_029.outputs[16].hide = True
    input_point_radius_029.outputs[17].hide = True
    input_point_radius_029.outputs[18].hide = True
    input_point_radius_029.outputs[19].hide = True
    input_point_radius_029.outputs[20].hide = True
    input_point_radius_029.outputs[21].hide = True
    input_point_radius_029.outputs[22].hide = True
    input_point_radius_029.outputs[23].hide = True
    input_point_radius_029.outputs[24].hide = True
    input_point_radius_029.outputs[25].hide = True
    input_point_radius_029.outputs[26].hide = True
    input_point_radius_029.outputs[27].hide = True
    input_point_radius_029.outputs[28].hide = True
    input_point_radius_029.outputs[29].hide = True
    input_point_radius_029.outputs[30].hide = True
    input_point_radius_029.outputs[31].hide = True
    input_point_radius_029.outputs[32].hide = True
    input_point_radius_029.outputs[33].hide = True
    input_point_radius_029.outputs[34].hide = True
    input_point_radius_029.outputs[35].hide = True
    input_point_radius_029.outputs[36].hide = True
    input_point_radius_029.outputs[38].hide = True
    input_point_radius_029.outputs[39].hide = True
    input_point_radius_029.outputs[40].hide = True

    # Node 已命名属性.003
    ______003_3 = ugrs_mainnodetree_v1_0_1.nodes.new("GeometryNodeInputNamedAttribute")
    ______003_3.name = "已命名属性.003"
    ______003_3.data_type = 'FLOAT'
    # Name
    ______003_3.inputs[0].default_value = "computeAlpha"

    # Node Reroute
    reroute = ugrs_mainnodetree_v1_0_1.nodes.new("NodeReroute")
    reroute.name = "Reroute"
    reroute.socket_idname = "NodeSocketGeometry"
    # Node 运算.023
    ___023 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeMath")
    ___023.name = "运算.023"
    ___023.operation = 'POWER'
    ___023.use_clamp = False
    # Value_001
    ___023.inputs[1].default_value = 2.0

    # Node 矢量运算.015
    _____015 = ugrs_mainnodetree_v1_0_1.nodes.new("ShaderNodeVectorMath")
    _____015.name = "矢量运算.015"
    _____015.operation = 'MAXIMUM'
    # Vector_001
    _____015.inputs[1].default_value = (9.999999974752427e-07, 9.999999974752427e-07, 9.999999974752427e-07)

    # Process zone input Simulation Input
    simulation_input.pair_with_output(simulation_output)
    # Item_1
    simulation_input.inputs[0].default_value = 0.0

    # Skip
    simulation_output.inputs[0].default_value = False


    # Process zone input 重复输入
    _____1.pair_with_output(_____2)
    # Item_1
    _____1.inputs[2].default_value = ""

    # Item_1
    _____2.inputs[1].default_value = ""

    # Process zone input 重复输入.001
    _____001_8.pair_with_output(_____001_9)
    # Item_0
    _____001_8.inputs[1].default_value = (0.5, 0.5, 0.5)



    # Set parents
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Index"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Compare"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Group Input"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["Simulation Input"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["Simulation Output"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.003"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["群组"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.012"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.013"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.014"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.015"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.004"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.016"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.004"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.017"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.004"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.018"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.004"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.008"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.009"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.014"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.001"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.015"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.001"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.016"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.001"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.017"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.001"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.018"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.001"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.020"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.006"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.025"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.006"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.026"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.006"]
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.027"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.006"]
    ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["群组.002"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.006"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.008"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.009"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.029"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.011"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Index.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.032"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["切换.003"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.033"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.040"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.007"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.012"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.026"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.024"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.041"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.042"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["群组.003"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.010"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.035"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["Group Input.004"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.010"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.004"]
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["组输入.013"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.008"]
    ugrs_mainnodetree_v1_0_1.nodes["切换.018"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]
    ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["运算.100"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧"]
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.015"].parent = ugrs_mainnodetree_v1_0_1.nodes["帧.003"]

    # Set locations
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info"].location = (1037.77783203125, -36.1260986328125)
    ugrs_mainnodetree_v1_0_1.nodes["Index"].location = (1033.86181640625, -210.4959716796875)
    ugrs_mainnodetree_v1_0_1.nodes["Compare"].location = (1213.861328125, -210.4959716796875)
    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].location = (1395.1669921875, -130.18310546875)
    ugrs_mainnodetree_v1_0_1.nodes["Group Input"].location = (286.427734375, -36.191650390625)
    ugrs_mainnodetree_v1_0_1.nodes["Simulation Input"].location = (40.6416015625, -506.305908203125)
    ugrs_mainnodetree_v1_0_1.nodes["Simulation Output"].location = (692.5341796875, -476.009765625)
    ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].location = (420.4384765625, -510.1434326171875)
    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply"].location = (248.0439453125, -459.762451171875)
    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply.001"].location = (956.5439453125, -428.6031494140625)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.001"].location = (842.18359375, -37.0693359375)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.003"].location = (30.0302734375, -355.1539306640625)
    ugrs_mainnodetree_v1_0_1.nodes["帧"].location = (-10143.0, -1111.5)
    ugrs_mainnodetree_v1_0_1.nodes["群组"].location = (1278.5732421875, -289.34619140625)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].location = (386.0966796875, -286.7294921875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.012"].location = (33.95458984375, -445.7529296875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.013"].location = (30.2177734375, -673.2783203125)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.014"].location = (31.50146484375, -315.55029296875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.015"].location = (29.8076171875, -54.9915771484375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.016"].location = (33.486328125, -187.5052490234375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.017"].location = (31.033203125, -320.016357421875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.018"].location = (33.6845703125, -448.677978515625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.008"].location = (501.61328125, -521.3310546875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.009"].location = (500.25390625, -564.85107421875)
    ugrs_mainnodetree_v1_0_1.nodes["立方体.001"].location = (8330.9541015625, -1222.5074462890625)
    ugrs_mainnodetree_v1_0_1.nodes["设置位置.001"].location = (858.2540283203125, -1595.6531982421875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.019"].location = (-147.10421752929688, -1925.8076171875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.020"].location = (-148.18820190429688, -2055.968017578125)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.021"].location = (-149.27218627929688, -2192.636474609375)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].location = (36.463165283203125, -2029.841796875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.022"].location = (-3117.7685546875, -1029.76318359375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.010"].location = (579.5074462890625, -1992.447509765625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.012"].location = (376.7623596191406, -2095.539794921875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.023"].location = (208.41128540039062, -2136.303955078125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.013"].location = (-2950.109619140625, -1029.3177490234375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.014"].location = (29.836669921875, -75.89990234375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.015"].location = (202.821044921875, -36.14202880859375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.016"].location = (361.0654296875, -40.4920654296875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.017"].location = (535.81982421875, -54.3397216796875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.018"].location = (689.51220703125, -63.43902587890625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.024"].location = (-3237.548828125, -846.9672241210938)
    ugrs_mainnodetree_v1_0_1.nodes["运算.020"].location = (877.5947265625, -443.57763671875)
    ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].location = (9241.2119140625, -658.6007080078125)
    ugrs_mainnodetree_v1_0_1.nodes["轴向 转换为 旋转.002"].location = (8099.56298828125, -818.5389404296875)
    ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].location = (8083.85791015625, -456.7931823730469)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.012"].location = (8989.556640625, -842.4063720703125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.021"].location = (7721.07177734375, -551.0625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.022"].location = (7719.63818359375, -710.24267578125)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].location = (231.91455078125, -69.817138671875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.025"].location = (30.19580078125, -29.810546875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.026"].location = (33.92529296875, -160.84912109375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.027"].location = (32.62353515625, -292.81103515625)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].location = (10818.7451171875, -1264.619384765625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.001"].location = (-5110.49609375, -2010.7491455078125)
    ugrs_mainnodetree_v1_0_1.nodes["帧.001"].location = (-3077.5, -770.5)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].location = (210.703125, -349.3692626953125)
    ugrs_mainnodetree_v1_0_1.nodes["群组.002"].location = (1754.8232421875, -217.8421630859375)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.006"].location = (1741.4794921875, -109.7235107421875)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.008"].location = (835.9453125, -415.2802734375)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.001"].location = (1031.38134765625, -293.2523193359375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].location = (357.404296875, -142.9580078125)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.006"].location = (-5104.12744140625, -2123.78857421875)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.003"].location = (10603.111328125, -1228.909423828125)
    ugrs_mainnodetree_v1_0_1.nodes["切换.001"].location = (1052.86962890625, -1397.505615234375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.005"].location = (7399.36669921875, -559.9931030273438)
    ugrs_mainnodetree_v1_0_1.nodes["运算.027"].location = (7724.42236328125, -396.8174133300781)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.009"].location = (1815.00341796875, -904.4833984375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.007"].location = (-5127.68408203125, -1750.6292724609375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].location = (215.10546875, -1079.51318359375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.029"].location = (1815.04931640625, -855.3887939453125)
    ugrs_mainnodetree_v1_0_1.nodes["帧.003"].location = (5266.0, -2703.0)
    ugrs_mainnodetree_v1_0_1.nodes["帧.004"].location = (4619.5, -1805.0)
    ugrs_mainnodetree_v1_0_1.nodes["帧.006"].location = (7558.0, -1011.5)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.009"].location = (-5113.41650390625, -857.9666137695312)
    ugrs_mainnodetree_v1_0_1.nodes["帧.008"].location = (-8496.0, -1119.5)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].location = (4060.23388671875, -1590.851318359375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].location = (703.798828125, -30.22021484375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.007"].location = (8648.2490234375, -267.9177551269531)
    ugrs_mainnodetree_v1_0_1.nodes["切换.002"].location = (8655.8828125, -348.7756042480469)
    ugrs_mainnodetree_v1_0_1.nodes["合并几何.002"].location = (8654.6376953125, -516.9642944335938)
    ugrs_mainnodetree_v1_0_1.nodes["变换几何体"].location = (8474.0771484375, -374.2134094238281)
    ugrs_mainnodetree_v1_0_1.nodes["帧.010"].location = (-2594.5, -569.5)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.004"].location = (-2760.57861328125, -571.7891845703125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.039"].location = (-2175.28857421875, -710.9735107421875)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.008"].location = (-1387.41943359375, -779.9930419921875)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].location = (-1206.038818359375, -778.654296875)
    ugrs_mainnodetree_v1_0_1.nodes["棱角球"].location = (8331.1748046875, -1264.62548828125)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.011"].location = (511.5263671875, -552.6981201171875)
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info.001"].location = (676.44970703125, -542.9827880859375)
    ugrs_mainnodetree_v1_0_1.nodes["Index.001"].location = (511.60009765625, -698.574462890625)
    ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].location = (692.20556640625, -713.930419921875)
    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].location = (874.90576171875, -627.0306396484375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.032"].location = (276.322265625, -881.6275634765625)
    ugrs_mainnodetree_v1_0_1.nodes["切换.003"].location = (1655.63720703125, -816.6895751953125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.033"].location = (1652.58544921875, -971.77099609375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.040"].location = (441.92626953125, -889.7100830078125)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.007"].location = (697.1455078125, -347.5533447265625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].location = (1299.73193359375, -1068.78466796875)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.012"].location = (29.765625, -1062.79638671875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.026"].location = (1116.1376953125, -308.06787109375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.012"].location = (8344.75390625, -895.1691284179688)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.014"].location = (8352.80078125, -1002.5093383789062)
    ugrs_mainnodetree_v1_0_1.nodes["切换.004"].location = (8523.6552734375, -904.75927734375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.024"].location = (203.62646484375, -333.78076171875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.041"].location = (209.96826171875, -473.38037109375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.042"].location = (207.40087890625, -660.38330078125)
    ugrs_mainnodetree_v1_0_1.nodes["群组.003"].location = (29.94482421875, -35.81048583984375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.035"].location = (1188.0, -57.677734375)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.020"].location = (2908.3310546875, -1212.6282958984375)
    ugrs_mainnodetree_v1_0_1.nodes["实现实例.004"].location = (11011.16015625, -1274.482421875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.010"].location = (829.3984375, -2090.0439453125)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.017"].location = (1646.8770751953125, -1514.82568359375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.018"].location = (1647.8028564453125, -1647.0406494140625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.019"].location = (1640.239013671875, -1378.8592529296875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.020"].location = (7468.63330078125, -1319.222412109375)
    ugrs_mainnodetree_v1_0_1.nodes["重复输入"].location = (-2869.236572265625, -1324.3360595703125)
    ugrs_mainnodetree_v1_0_1.nodes["重复输出"].location = (-1317.397216796875, -1499.76611328125)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.006"].location = (-1872.065185546875, -1279.5185546875)
    ugrs_mainnodetree_v1_0_1.nodes["字符串"].location = (-2626.78759765625, -1425.948974609375)
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串"].location = (-2026.180419921875, -1280.4736328125)
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串"].location = (-2198.964599609375, -1273.72265625)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算"].location = (-2356.574462890625, -1274.56884765625)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.001"].location = (-2355.621337890625, -1409.0283203125)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.002"].location = (-2355.621337890625, -1539.6728515625)
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.001"].location = (-2194.200439453125, -1408.18212890625)
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.002"].location = (-2195.153076171875, -1548.36279296875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.007"].location = (-1873.017822265625, -1408.25634765625)
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.001"].location = (-2027.133544921875, -1409.2109375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.008"].location = (-1876.829345703125, -1541.76171875)
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.002"].location = (-2030.945068359375, -1542.716796875)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].location = (-1317.18603515625, -1278.9681396484375)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.004"].location = (-2452.436279296875, -1733.62060546875)
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.003"].location = (-2251.154052734375, -1731.83740234375)
    ugrs_mainnodetree_v1_0_1.nodes["字符串.001"].location = (-2085.933349609375, -1733.48388671875)
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.003"].location = (-1910.662353515625, -1734.77294921875)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].location = (-1506.082275390625, -1412.9373779296875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].location = (-2444.547607421875, -1460.2996826171875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.009"].location = (-3641.536865234375, -1467.087158203125)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.010"].location = (-3642.489501953125, -1595.824462890625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.011"].location = (-3646.301025390625, -1729.330322265625)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.022"].location = (-3267.228271484375, -1310.0164794921875)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].location = (-3273.085693359375, -1523.9876708984375)
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.003"].location = (-4389.34130859375, -1459.799560546875)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.004"].location = (-4853.49951171875, -1827.214599609375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.003"].location = (-4494.05224609375, -1867.28271484375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.036"].location = (-4498.80615234375, -1907.937255859375)
    ugrs_mainnodetree_v1_0_1.nodes["位置.007"].location = (-4687.57763671875, -1752.1280517578125)
    ugrs_mainnodetree_v1_0_1.nodes["实现实例.003"].location = (-5339.73291015625, -1383.9334716796875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.025"].location = (9340.2978515625, -1646.6932373046875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.027"].location = (-5418.11865234375, -1407.71875)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.023"].location = (-6000.16748046875, -1135.525390625)
    ugrs_mainnodetree_v1_0_1.nodes["切换.006"].location = (-5780.8125, -1309.0352783203125)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.014"].location = (-5789.11328125, -1231.589111328125)
    ugrs_mainnodetree_v1_0_1.nodes["Group Input.004"].location = (701.2900390625, -250.648681640625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.010"].location = (957.8876953125, -372.2254638671875)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.017"].location = (-3121.4365234375, -1777.6673583984375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.036"].location = (-2920.35107421875, -1501.0906982421875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.037"].location = (-2916.411865234375, -1381.6373291015625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].location = (-2425.812744140625, -1356.3424072265625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.039"].location = (-2931.285400390625, -1623.0255126953125)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.003"].location = (-3118.27001953125, -1720.2034912109375)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.005"].location = (-3115.651611328125, -1665.1678466796875)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.006"].location = (-3110.414794921875, -1611.005615234375)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.007"].location = (-2749.045166015625, -1624.8170166015625)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.018"].location = (3338.404296875, -1491.78515625)
    ugrs_mainnodetree_v1_0_1.nodes["切换.008"].location = (-833.90966796875, -1362.0242919921875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.022"].location = (-3585.952392578125, -1218.437744140625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.023"].location = (-1099.314453125, -1206.4078369140625)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].location = (9250.5458984375, -1810.4022216796875)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.019"].location = (8969.8310546875, -1851.5802001953125)
    ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].location = (9613.865234375, -1363.5767822265625)
    ugrs_mainnodetree_v1_0_1.nodes["设置着色平滑.001"].location = (8991.109375, -1461.5374755859375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.041"].location = (8213.2890625, -1437.5067138671875)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.018"].location = (3123.0712890625, -1247.3707275390625)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].location = (6768.76220703125, -1405.956787109375)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].location = (6947.58154296875, -1415.355712890625)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].location = (7138.18896484375, -1418.532470703125)
    ugrs_mainnodetree_v1_0_1.nodes["逆矩阵.002"].location = (6336.09375, -1668.772216796875)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.028"].location = (6786.49072265625, -1211.467529296875)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.029"].location = (6966.69580078125, -1220.332763671875)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.030"].location = (7141.63525390625, -1231.73046875)
    ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].location = (6563.19091796875, -1434.094482421875)
    ugrs_mainnodetree_v1_0_1.nodes["转置矩阵.003"].location = (6334.99609375, -1790.767822265625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.056"].location = (8917.3740234375, -2031.7930908203125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.057"].location = (9077.8056640625, -2028.7711181640625)
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].location = (8712.25390625, -2110.468017578125)
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.007"].location = (-651.1627197265625, -1365.8017578125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.059"].location = (-647.2265625, -1232.426025390625)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.020"].location = (-653.083984375, -1155.6136474609375)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.004"].location = (-1005.978515625, -1263.019287109375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.021"].location = (-1169.131103515625, -1264.7379150390625)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.026"].location = (-2482.419677734375, -1104.1639404296875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.032"].location = (-2686.808837890625, -1206.0340576171875)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.005"].location = (1408.7188720703125, -1767.005615234375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.022"].location = (1225.6968994140625, -1777.658447265625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点"].location = (1792.1162109375, -1374.661376953125)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.002"].location = (-2928.14599609375, -664.2739868164062)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.008"].location = (-4497.6591796875, -1778.03759765625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.009"].location = (-4499.21240234375, -1825.91650390625)
    ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].location = (409.466796875, -30.0240478515625)
    ugrs_mainnodetree_v1_0_1.nodes["对偶网格"].location = (8155.3662109375, -1410.0706787109375)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].location = (689.865234375, -791.717041015625)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.013"].location = (508.20166015625, -768.8116455078125)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.014"].location = (8967.8818359375, -1654.35498046875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.051"].location = (9211.552734375, -1691.02978515625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.011"].location = (580.0244140625, -3014.940185546875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.016"].location = (383.888671875, -3248.235107421875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.017"].location = (570.087890625, -3245.681396484375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.018"].location = (378.109375, -3597.907958984375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.042"].location = (564.30859375, -3595.355224609375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.044"].location = (375.72998046875, -3960.676513671875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.045"].location = (561.92919921875, -3958.122802734375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.019"].location = (381.31591796875, -4546.171875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.043"].location = (567.51513671875, -4543.6181640625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.046"].location = (375.53662109375, -4895.8447265625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.047"].location = (561.73583984375, -4893.2919921875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.048"].location = (373.1572265625, -5258.61328125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.049"].location = (559.3564453125, -5256.0595703125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.044"].location = (23.07861328125, -5459.61328125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.058"].location = (207.1474609375, -5529.59375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.061"].location = (376.87890625, -5604.1318359375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.050"].location = (375.630859375, -5897.6005859375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.051"].location = (561.830078125, -5895.046875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.052"].location = (385.52490234375, -6241.4169921875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.053"].location = (571.72412109375, -6238.86328125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.062"].location = (196.95556640625, -6434.060546875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.020"].location = (1109.8192138671875, -3236.5380859375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.021"].location = (1112.5802001953125, -3587.224365234375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.054"].location = (1111.4757080078125, -3440.993408203125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.055"].location = (1134.88525390625, -3794.626953125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.057"].location = (1136.10009765625, -4075.251953125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.058"].location = (1134.65185546875, -3932.4794921875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.059"].location = (1145.22998046875, -4214.248046875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.061"].location = (388.7939453125, -7045.4208984375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.062"].location = (574.9931640625, -7042.8681640625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.063"].location = (187.71240234375, -7282.5234375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.064"].location = (348.15283203125, -7341.90625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.065"].location = (508.59326171875, -7385.6630859375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.063"].location = (386.23193359375, -7735.029296875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.064"].location = (572.43115234375, -7732.4765625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.066"].location = (185.15087890625, -7972.1318359375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.065"].location = (380.63330078125, -8504.859375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.066"].location = (566.83251953125, -8502.306640625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.067"].location = (166.87646484375, -8743.150390625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.068"].location = (342.94384765625, -8824.4111328125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.069"].location = (524.220703125, -8876.5029296875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.070"].location = (696.12158203125, -8920.2587890625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.067"].location = (401.47021484375, -9157.0361328125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.068"].location = (587.66943359375, -9154.4833984375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.071"].location = (189.79638671875, -9299.48046875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.072"].location = (414.82958984375, -9398.451171875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.073"].location = (596.1064453125, -9450.54296875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.074"].location = (196.04736328125, -9473.4638671875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.075"].location = (192.92236328125, -9643.2802734375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.076"].location = (769.04931640625, -9450.544921875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.069"].location = (378.5498046875, -10082.1787109375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.070"].location = (564.7490234375, -10079.625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.077"].location = (164.79248046875, -10320.4697265625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.078"].location = (340.85986328125, -10401.73046875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.079"].location = (522.13720703125, -10453.822265625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.080"].location = (694.03759765625, -10497.578125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.071"].location = (384.80078125, -10809.3720703125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.072"].location = (571.0, -10806.8193359375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.081"].location = (199.17138671875, -11067.4560546875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.082"].location = (380.44775390625, -11109.12890625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.073"].location = (378.5498046875, -11538.65234375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.074"].location = (564.7490234375, -11536.099609375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.083"].location = (400.24560546875, -11802.9873046875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.084"].location = (642.99072265625, -11872.7890625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.085"].location = (220.00537109375, -11929.048828125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.075"].location = (1288.6993408203125, -6183.04541015625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.077"].location = (1303.5489501953125, -6479.0087890625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.078"].location = (1300.3966064453125, -6334.53271484375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.079"].location = (1300.7481689453125, -6623.11767578125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.080"].location = (1296.8292236328125, -6766.14111328125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.081"].location = (1290.6202392578125, -6910.25048828125)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.028"].location = (109.655517578125, -3011.27197265625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.031"].location = (113.739013671875, -3252.156982421875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.033"].location = (107.852783203125, -3594.965087890625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.034"].location = (119.625244140625, -3949.54345703125)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.035"].location = (91.66552734375, -4538.05615234375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.036"].location = (91.66552734375, -4883.8076171875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.037"].location = (97.5517578125, -5272.2265625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.038"].location = (99.271728515625, -5884.3837890625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.039"].location = (90.672119140625, -6233.45166015625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.040"].location = (90.672119140625, -7038.19921875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.041"].location = (106.15087890625, -7736.3349609375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.042"].location = (87.232177734375, -8510.1318359375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.043"].location = (104.430908203125, -9153.2431640625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.044"].location = (104.430908203125, -10093.837890625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.045"].location = (111.310302734375, -10828.0869140625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.046"].location = (92.3916015625, -11534.8232421875)
    ugrs_mainnodetree_v1_0_1.nodes["群组.004"].location = (-90.72314453125, -3275.0986328125)
    ugrs_mainnodetree_v1_0_1.nodes["群组.005"].location = (-96.110107421875, -3660.7255859375)
    ugrs_mainnodetree_v1_0_1.nodes["群组.007"].location = (-100.41943359375, -3972.027587890625)
    ugrs_mainnodetree_v1_0_1.nodes["群组.008"].location = (-130.5859375, -4595.71044921875)
    ugrs_mainnodetree_v1_0_1.nodes["群组.009"].location = (-131.663330078125, -4939.3291015625)
    ugrs_mainnodetree_v1_0_1.nodes["群组.010"].location = (-178.988037109375, -5477.14990234375)
    ugrs_mainnodetree_v1_0_1.nodes["群组.011"].location = (-169.523193359375, -5862.7724609375)
    ugrs_mainnodetree_v1_0_1.nodes["群组.012"].location = (-164.790771484375, -6253.9150390625)
    ugrs_mainnodetree_v1_0_1.nodes["群组.013"].location = (-148.41162109375, -7117.05224609375)
    ugrs_mainnodetree_v1_0_1.nodes["群组.014"].location = (-129.8916015625, -7813.19921875)
    ugrs_mainnodetree_v1_0_1.nodes["群组.015"].location = (-126.81982421875, -8762.6396484375)
    ugrs_mainnodetree_v1_0_1.nodes["群组.016"].location = (-102.90185546875, -9332.578125)
    ugrs_mainnodetree_v1_0_1.nodes["群组.017"].location = (-51.89990234375, -10411.3955078125)
    ugrs_mainnodetree_v1_0_1.nodes["群组.018"].location = (-43.92724609375, -11048.0947265625)
    ugrs_mainnodetree_v1_0_1.nodes["群组.019"].location = (-28.978515625, -11727.6396484375)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.032"].location = (4619.72216796875, -1348.331787109375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.003"].location = (-3580.300048828125, -1410.56298828125)
    ugrs_mainnodetree_v1_0_1.nodes["切换.010"].location = (-4172.87158203125, -1371.227783203125)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.023"].location = (-4347.51025390625, -1302.1016845703125)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.024"].location = (-5068.30712890625, -1989.8167724609375)
    ugrs_mainnodetree_v1_0_1.nodes["自身物体"].location = (-6382.54833984375, -1224.698974609375)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.006"].location = (-6210.8076171875, -1223.5062255859375)
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.001"].location = (5720.68505859375, -1599.0758056640625)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.007"].location = (5892.42626953125, -1597.8831787109375)
    ugrs_mainnodetree_v1_0_1.nodes["投影点"].location = (2903.495849609375, -1391.7030029296875)
    ugrs_mainnodetree_v1_0_1.nodes["合并变换.001"].location = (6129.26171875, -1788.615966796875)
    ugrs_mainnodetree_v1_0_1.nodes["矩阵相乘.003"].location = (6133.22314453125, -1655.61279296875)
    ugrs_mainnodetree_v1_0_1.nodes["旋转矢量"].location = (-4690.9853515625, -1825.57666015625)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.002"].location = (-4887.5888671875, -2214.36328125)
    ugrs_mainnodetree_v1_0_1.nodes["位置.010"].location = (-4883.220703125, -2131.27783203125)
    ugrs_mainnodetree_v1_0_1.nodes["光线投射"].location = (-4265.63525390625, -1895.1082763671875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.022"].location = (-4586.169921875, -2214.4267578125)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.054"].location = (-4700.59033203125, -2178.22119140625)
    ugrs_mainnodetree_v1_0_1.nodes["布尔运算"].location = (-4174.3369140625, -1745.8338623046875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.086"].location = (9664.0791015625, -1769.7587890625)
    ugrs_mainnodetree_v1_0_1.nodes["Camera Info"].location = (1238.9326171875, -817.38720703125)
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.008"].location = (2577.09033203125, -1063.9989013671875)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.008"].location = (1240.4384765625, -447.4478759765625)
    ugrs_mainnodetree_v1_0_1.nodes["变换点.001"].location = (1408.63427734375, -652.94384765625)
    ugrs_mainnodetree_v1_0_1.nodes["逆矩阵"].location = (1422.23388671875, -478.7764892578125)
    ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].location = (1608.234375, -671.22607421875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.001"].location = (1602.2110595703125, -578.7521362304688)
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.002"].location = (850.23876953125, -739.35107421875)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.009"].location = (1021.97998046875, -738.158447265625)
    ugrs_mainnodetree_v1_0_1.nodes["投影点.002"].location = (1211.005859375, -677.7097778320312)
    ugrs_mainnodetree_v1_0_1.nodes["位置.011"].location = (1022.97998046875, -619.01025390625)
    ugrs_mainnodetree_v1_0_1.nodes["组输入"].location = (2360.545654296875, -1210.9136962890625)
    ugrs_mainnodetree_v1_0_1.nodes["切换.012"].location = (2534.686767578125, -1250.4093017578125)
    ugrs_mainnodetree_v1_0_1.nodes["组输出"].location = (11397.0810546875, -1267.311279296875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.023"].location = (9360.4384765625, -1513.3565673828125)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.026"].location = (8503.6826171875, -1222.0682373046875)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].location = (8505.94140625, -1290.700927734375)
    ugrs_mainnodetree_v1_0_1.nodes["Mesh to Points.003"].location = (10265.7744140625, -1511.7213134765625)
    ugrs_mainnodetree_v1_0_1.nodes["位置.004"].location = (2671.343994140625, -1391.962646484375)
    ugrs_mainnodetree_v1_0_1.nodes["删除已命名属性"].location = (-1329.3349609375, -1632.75537109375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.011"].location = (3489.94921875, -3841.83984375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.027"].location = (4629.18359375, -1265.97119140625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.028"].location = (5205.08642578125, -1258.936279296875)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.029"].location = (2028.859130859375, -1826.2554931640625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.030"].location = (2027.775146484375, -1956.416015625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.047"].location = (2026.691162109375, -2093.08447265625)
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].location = (2212.426513671875, -1930.2896728515625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.032"].location = (3340.30224609375, -1574.3978271484375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.034"].location = (3063.88330078125, -2024.3765869140625)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.028"].location = (3058.80810546875, -1753.5489501953125)
    ugrs_mainnodetree_v1_0_1.nodes["切换.013"].location = (3415.544189453125, -1784.0684814453125)
    ugrs_mainnodetree_v1_0_1.nodes["切换.014"].location = (3235.485595703125, -1774.7340087890625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.035"].location = (3059.753173828125, -1890.6878662109375)
    ugrs_mainnodetree_v1_0_1.nodes["设置材质"].location = (11202.2314453125, -1269.8236083984375)
    ugrs_mainnodetree_v1_0_1.nodes["切换.017"].location = (4916.970703125, -1237.6572265625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.036"].location = (185.51571655273438, -1866.014404296875)
    ugrs_mainnodetree_v1_0_1.nodes["运算.028"].location = (355.43975830078125, -1752.662841796875)
    ugrs_mainnodetree_v1_0_1.nodes["元素排序"].location = (6125.0556640625, -1231.6494140625)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.012"].location = (3694.290283203125, -1394.3701171875)
    ugrs_mainnodetree_v1_0_1.nodes["位置.005"].location = (3684.855224609375, -1313.6533203125)
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.001"].location = (3513.111083984375, -1532.9755859375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.037"].location = (3877.146728515625, -1440.2747802734375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.001"].location = (5943.32470703125, -1361.15869140625)
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.002"].location = (5677.84716796875, -1191.844482421875)
    ugrs_mainnodetree_v1_0_1.nodes["烘焙.002"].location = (53.34635925292969, -1441.3963623046875)
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.010"].location = (637.6759643554688, -1586.1224365234375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.001"].location = (3556.920166015625, -2562.1494140625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.060"].location = (3544.40673828125, -2799.96923828125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.087"].location = (3716.64013671875, -2783.2490234375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.088"].location = (3877.58203125, -2794.083984375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.094"].location = (3857.45751953125, -2591.36572265625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.095"].location = (4043.492431640625, -2530.12548828125)
    ugrs_mainnodetree_v1_0_1.nodes["曲线圆环"].location = (8325.78125, -1621.11083984375)
    ugrs_mainnodetree_v1_0_1.nodes["填充曲线.004"].location = (8509.3408203125, -1621.956298828125)
    ugrs_mainnodetree_v1_0_1.nodes["切换.018"].location = (477.884765625, -660.05615234375)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.004"].location = (8153.35546875, -1548.7606201171875)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].location = (8739.7060546875, -1463.663330078125)
    ugrs_mainnodetree_v1_0_1.nodes["编号切换"].location = (2213.1494140625, -3961.289794921875)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.010"].location = (1476.548828125, -3652.281005859375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].location = (-2290.48388671875, -635.4042358398438)
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.003"].location = (3611.683349609375, -1157.998291015625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.029"].location = (3448.182861328125, -1051.998291015625)
    ugrs_mainnodetree_v1_0_1.nodes["群组.020"].location = (2851.406982421875, -2100.1240234375)
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.004"].location = (2639.637939453125, -1499.4425048828125)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.013"].location = (2811.379150390625, -1498.2498779296875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.042"].location = (3380.426513671875, -1303.3505859375)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.016"].location = (1478.9803466796875, -3569.66357421875)
    ugrs_mainnodetree_v1_0_1.nodes["重复输入.001"].location = (1867.96923828125, -3790.717529296875)
    ugrs_mainnodetree_v1_0_1.nodes["重复输出.001"].location = (2592.861328125, -3834.6044921875)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.010"].location = (1674.9561767578125, -3571.355224609375)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.011"].location = (1856.51513671875, -3632.369384765625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.084"].location = (2419.482421875, -3876.385498046875)
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.012"].location = (2211.555419921875, -3812.931396484375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.089"].location = (-788.0347900390625, -1077.741943359375)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.006"].location = (-969.8878173828125, -1060.9559326171875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.013"].location = (5418.70654296875, -1861.3262939453125)
    ugrs_mainnodetree_v1_0_1.nodes["变换几何体.001"].location = (8324.1240234375, -1446.3468017578125)
    ugrs_mainnodetree_v1_0_1.nodes["运算.007"].location = (2006.304443359375, -491.2445373535156)
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].location = (1794.6016845703125, -731.3245239257812)
    ugrs_mainnodetree_v1_0_1.nodes["运算.019"].location = (2004.2703857421875, -670.2724609375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.030"].location = (2002.236572265625, -847.2659912109375)
    ugrs_mainnodetree_v1_0_1.nodes["布尔运算.004"].location = (2175.205322265625, -634.6187744140625)
    ugrs_mainnodetree_v1_0_1.nodes["布尔运算.005"].location = (2174.0185546875, -835.918212890625)
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.010"].location = (1426.0047607421875, -1557.0423583984375)
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.003"].location = (1034.6546630859375, -1039.3897705078125)
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.004"].location = (1023.4987182617188, -489.8973388671875)
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.005"].location = (2243.002685546875, -2192.257568359375)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.014"].location = (2414.743896484375, -2191.065185546875)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].location = (2799.552734375, -1897.30322265625)
    ugrs_mainnodetree_v1_0_1.nodes["变换方向"].location = (2419.67724609375, -1890.76416015625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.015"].location = (1022.4348754882812, -3054.119140625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.085"].location = (4218.37548828125, -1368.1668701171875)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.086"].location = (4221.0625, -1417.61962890625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].location = (6113.44384765625, -2446.879150390625)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.055"].location = (2992.236083984375, -2758.3203125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.033"].location = (3305.282958984375, -2294.133056640625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.039"].location = (3460.492431640625, -2282.77001953125)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].location = (3204.246826171875, -2605.886474609375)
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.008"].location = (2418.327392578125, -2525.49267578125)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.018"].location = (2587.8369140625, -2379.25927734375)
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.007"].location = (2635.021484375, -2743.32177734375)
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.019"].location = (2794.93359375, -2743.3212890625)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.040"].location = (2980.693359375, -2603.281982421875)
    ugrs_mainnodetree_v1_0_1.nodes["位置.006"].location = (2579.706298828125, -2613.82958984375)
    ugrs_mainnodetree_v1_0_1.nodes["投影点.006"].location = (2780.924072265625, -2615.57861328125)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].location = (4391.88525390625, -1339.836181640625)
    ugrs_mainnodetree_v1_0_1.nodes["组输入.017"].location = (4397.044921875, -1238.9166259765625)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].location = (868.8486328125, -207.29541015625)
    ugrs_mainnodetree_v1_0_1.nodes["运算.100"].location = (518.8681640625, -192.04736328125)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].location = (694.447265625, -176.734375)
    ugrs_mainnodetree_v1_0_1.nodes["转接点.045"].location = (552.4547729492188, -1489.6085205078125)
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].location = (3884.864990234375, -1266.589111328125)
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.029"].location = (3889.499755859375, -1158.3583984375)
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.003"].location = (3642.986572265625, -1662.9638671875)
    ugrs_mainnodetree_v1_0_1.nodes["Reroute"].location = (-4457.3603515625, -1422.38037109375)
    ugrs_mainnodetree_v1_0_1.nodes["运算.023"].location = (-2776.348388671875, -1032.7591552734375)
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.015"].location = (594.0, -277.0)

    # Set dimensions
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Index"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Index"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Compare"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Compare"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Group Input"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Group Input"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Simulation Input"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Simulation Input"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Simulation Output"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Simulation Output"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["帧"].width  = 1448.5
    ugrs_mainnodetree_v1_0_1.nodes["帧"].height = 648.5

    ugrs_mainnodetree_v1_0_1.nodes["群组"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.015"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.015"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.016"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.016"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["立方体.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["立方体.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["设置位置.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["设置位置.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.019"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.020"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.021"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.021"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.022"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.022"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.023"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.023"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.015"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.015"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.016"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.016"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.024"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.024"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.020"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["轴向 转换为 旋转.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["轴向 转换为 旋转.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.021"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.021"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.022"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.022"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.025"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.025"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.026"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.026"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.027"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.027"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.001"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["帧.001"].width  = 859.5
    ugrs_mainnodetree_v1_0_1.nodes["帧.001"].height = 233.5

    ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.006"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.027"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.027"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.007"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.029"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.029"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["帧.003"].width  = 1358.0
    ugrs_mainnodetree_v1_0_1.nodes["帧.003"].height = 834.0

    ugrs_mainnodetree_v1_0_1.nodes["帧.004"].width  = 579.5
    ugrs_mainnodetree_v1_0_1.nodes["帧.004"].height = 600.5

    ugrs_mainnodetree_v1_0_1.nodes["帧.006"].width  = 402.0
    ugrs_mainnodetree_v1_0_1.nodes["帧.006"].height = 445.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.009"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["帧.008"].width  = 1985.0
    ugrs_mainnodetree_v1_0_1.nodes["帧.008"].height = 1151.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并几何.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并几何.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["变换几何体"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["变换几何体"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["帧.010"].width  = 200.0
    ugrs_mainnodetree_v1_0_1.nodes["帧.010"].height = 184.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.039"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.039"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["棱角球"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["棱角球"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.011"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Collection Info.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Collection Info.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Index.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Index.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.032"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.032"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.033"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.033"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.040"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.040"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.026"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.026"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.024"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.024"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.041"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.041"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.042"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.042"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.035"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.035"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.020"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["实现实例.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["实现实例.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.010"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.017"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.018"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.019"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.020"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["重复输入"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["重复输入"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["重复输出"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["重复输出"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["字符串"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["字符串"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并字符串"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["字符串.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["字符串.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并字符串.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.011"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.022"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.022"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.036"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.036"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["位置.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["位置.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["实现实例.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["实现实例.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.025"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.025"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.027"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.027"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.023"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.023"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Group Input.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Group Input.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.036"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.036"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.037"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.037"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.039"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.039"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.022"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.022"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.023"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.023"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.019"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["设置着色平滑.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["设置着色平滑.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.041"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.041"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["逆矩阵.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["逆矩阵.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.028"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.028"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.029"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.029"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.030"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.030"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转置矩阵.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["转置矩阵.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.056"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.056"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.057"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.057"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.059"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.059"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.020"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.021"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.021"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.026"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.026"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.032"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.032"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.022"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.022"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["对偶网格"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["对偶网格"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.051"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.051"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.011"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.016"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.016"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.042"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.042"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.044"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.044"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.045"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.045"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.019"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.043"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.043"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.046"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.046"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.047"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.047"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.048"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.048"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.049"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.049"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.044"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.044"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.058"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.058"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.061"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.061"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.050"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.050"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.051"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.051"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.052"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.052"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.053"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.053"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.062"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.062"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.020"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.021"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.021"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.054"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.054"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.055"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.055"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.057"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.057"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.058"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.058"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.059"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.059"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.061"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.061"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.062"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.062"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.063"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.063"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.064"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.064"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.065"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.065"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.063"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.063"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.064"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.064"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.066"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.066"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.065"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.065"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.066"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.066"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.067"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.067"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.068"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.068"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.069"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.069"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.070"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.070"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.067"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.067"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.068"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.068"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.071"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.071"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.072"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.072"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.073"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.073"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.074"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.074"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.075"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.075"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.076"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.076"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.069"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.069"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.070"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.070"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.077"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.077"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.078"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.078"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.079"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.079"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.080"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.080"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.071"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.071"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.072"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.072"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.081"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.081"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.082"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.082"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.073"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.073"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.074"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.074"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.083"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.083"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.084"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.084"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.085"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.085"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.075"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.075"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.077"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.077"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.078"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.078"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.079"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.079"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.080"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.080"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.081"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.081"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.028"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.028"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.031"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.031"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.033"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.033"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.034"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.034"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.035"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.035"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.036"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.036"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.037"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.037"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.038"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.038"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.039"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.039"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.040"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.040"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.041"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.041"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.042"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.042"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.043"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.043"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.044"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.044"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.045"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.045"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.046"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.046"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.011"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.015"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.015"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.016"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.016"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.019"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.032"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.032"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.003"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.023"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.023"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.024"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.024"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["自身物体"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["自身物体"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["自身物体.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["投影点"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["投影点"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并变换.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并变换.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矩阵相乘.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矩阵相乘.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["旋转矢量"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["旋转矢量"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["位置.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["位置.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["光线投射"].width  = 150.0
    ugrs_mainnodetree_v1_0_1.nodes["光线投射"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.022"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.022"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.054"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.054"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["布尔运算"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["布尔运算"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.086"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.086"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Camera Info"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Camera Info"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["变换点.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["变换点.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["逆矩阵"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["逆矩阵"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["自身物体.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["投影点.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["投影点.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["位置.011"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["位置.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输出"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输出"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.023"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.023"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.026"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.026"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Mesh to Points.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["Mesh to Points.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["位置.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["位置.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["删除已命名属性"].width  = 170.0
    ugrs_mainnodetree_v1_0_1.nodes["删除已命名属性"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.011"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.027"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.027"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.028"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.028"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.029"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.029"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.030"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.030"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.047"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.047"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.032"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.032"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.034"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.034"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.028"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.028"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.035"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.035"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["设置材质"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["设置材质"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.036"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.036"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.028"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.028"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["元素排序"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["元素排序"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["位置.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["位置.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.037"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.037"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["烘焙.002"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["烘焙.002"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["删除几何体.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.060"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.060"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.087"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.087"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.088"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.088"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.094"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.094"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.095"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.095"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["曲线圆环"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["曲线圆环"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["填充曲线.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["填充曲线.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["切换.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["切换.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["编号切换"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["编号切换"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.029"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.029"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["群组.020"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["群组.020"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["自身物体.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.013"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.042"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.042"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.016"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.016"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["重复输入.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["重复输入.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["重复输出.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["重复输出.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.011"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.011"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.084"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.084"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["整数运算.012"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["整数运算.012"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.089"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.089"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.013"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.013"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["变换几何体.001"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["变换几何体.001"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.019"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.030"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.030"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["布尔运算.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["布尔运算.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["布尔运算.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["布尔运算.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.004"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.004"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["自身物体.005"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.005"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.014"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["变换方向"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["变换方向"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.015"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.015"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.085"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.085"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.086"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.086"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.055"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.055"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.033"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.033"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.039"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.039"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["自身物体.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["自身物体.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.018"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.018"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.007"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.007"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["物体信息.019"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["物体信息.019"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.040"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.040"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["位置.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["位置.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["投影点.006"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["投影点.006"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["组输入.017"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["组输入.017"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.100"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.100"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["转接点.045"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["转接点.045"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.029"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.029"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.003"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["已命名属性.003"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["Reroute"].width  = 20.0
    ugrs_mainnodetree_v1_0_1.nodes["Reroute"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["运算.023"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["运算.023"].height = 100.0

    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.015"].width  = 140.0
    ugrs_mainnodetree_v1_0_1.nodes["矢量运算.015"].height = 100.0


    # Initialize ugrs_mainnodetree_v1_0_1 links

    # index.Index -> compare.A
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Index"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Compare"].inputs[2]
    )
    # collection_info.Instances -> delete_geometry.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Collection Info"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].inputs[0]
    )
    # compare.Result -> delete_geometry.Selection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Compare"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].inputs[1]
    )
    # simulation_input.Current Frame -> math_add.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Simulation Input"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].inputs[1]
    )
    # math_multiply.Value -> math_add.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].inputs[0]
    )
    # math_add.Value -> simulation_output.Current Frame
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Math_Add"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Simulation Output"].inputs[1]
    )
    # simulation_input.Delta Time -> math_multiply.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Simulation Input"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply"].inputs[1]
    )
    # group_input.Control Method -> __.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Group Input"].outputs[14],
        ugrs_mainnodetree_v1_0_1.nodes["群组"].inputs[0]
    )
    # ____044.Output -> __.Frame Index
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["群组"].inputs[1]
    )
    # ___008.Value -> ___009.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.009"].inputs[0]
    )
    # ______022.Attribute -> ___013.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.022"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.013"].inputs[0]
    )
    # ___017.Value -> ___018.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.018"].inputs[0]
    )
    # ______024.Attribute -> ___014.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.024"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.014"].inputs[1]
    )
    # __________002.Rotation -> _______003.Rotation
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["轴向 转换为 旋转.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].inputs[5]
    )
    # _____012.Value -> _______003.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.012"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].inputs[6]
    )
    # ___021.Value -> ___001.Radius Bottom
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].inputs[4]
    )
    # ___022.Value -> ___001.Depth
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.022"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].inputs[5]
    )
    # ___xyz_004.Vector -> __________002.Primary Axis
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["轴向 转换为 旋转.002"].inputs[0]
    )
    # ____020.Output -> _______003.Points
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.020"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].inputs[0]
    )
    # _______003.Instances -> ____.MotionLine
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].inputs[3]
    )
    # ____004.Output -> compare.B
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Compare"].inputs[3]
    )
    # delete_geometry.Geometry -> ___002.3dgs序列
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].inputs[1]
    )
    # ____006.Input format -> ___002.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.006"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].inputs[0]
    )
    # ____008.4DGS -> _____001_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.008"].outputs[6],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.001"].inputs[0]
    )
    # ___002._4D -> ____006_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.006"].inputs[0]
    )
    # input_point_radius_003.Display Mode -> ____.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.003"].outputs[21],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].inputs[0]
    )
    # input_point_radius_005.LineBottom -> ___021.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.005"].outputs[31],
        ugrs_mainnodetree_v1_0_1.nodes["运算.021"].inputs[0]
    )
    # input_point_radius_005.LineLenth -> ___022.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.005"].outputs[29],
        ugrs_mainnodetree_v1_0_1.nodes["运算.022"].inputs[0]
    )
    # input_point_radius_005.LineTop -> ___027.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.005"].outputs[30],
        ugrs_mainnodetree_v1_0_1.nodes["运算.027"].inputs[0]
    )
    # ___027.Value -> ___001.Radius Top
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.027"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].inputs[3]
    )
    # ___029.Value -> ____007.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.029"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.007"].inputs[0]
    )
    # ____004.Output -> ____008_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].inputs[0]
    )
    # ____007.Output -> ____009_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.009"].inputs[0]
    )
    # ____009_1.Output -> ___014.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.009"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.014"].inputs[0]
    )
    # ___012.Value -> _____010.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.012"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.010"].inputs[3]
    )
    # _____010.Vector -> _____001.Offset
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["设置位置.001"].inputs[3]
    )
    # ____007.Output -> ____001_2.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.001"].inputs[0]
    )
    # _____002.Geometry -> ___002_1.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并几何.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.002"].inputs[2]
    )
    # ___002_1.Output -> _______003.Instance
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.003"].inputs[2]
    )
    # ___001.Mesh -> _____.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["变换几何体"].inputs[0]
    )
    # ___001.Mesh -> _____002.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并几何.002"].inputs[0]
    )
    # ___001.Mesh -> ___002_1.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["锥形.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.002"].inputs[1]
    )
    # ____026.Output -> ___039.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.039"].inputs[0]
    )
    # ___018.Value -> ___039.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.039"].inputs[1]
    )
    # input_point_radius_008.AlphaClipMode -> _____002_1.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.008"].outputs[25],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].inputs[0]
    )
    # ____011.multi4DGS -> collection_info_001.Collection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.011"].outputs[7],
        ugrs_mainnodetree_v1_0_1.nodes["Collection Info.001"].inputs[0]
    )
    # index_001.Index -> compare_001.A
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Index.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].inputs[2]
    )
    # compare_001.Result -> delete_geometry_001.Selection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].inputs[1]
    )
    # collection_info_001.Instances -> delete_geometry_001.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Collection Info.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].inputs[0]
    )
    # delete_geometry_001.Geometry -> ___002.分段4dgs
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Delete Geometry.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].inputs[3]
    )
    # _____001_1.Geometry -> ___002.4dgs
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.001"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].inputs[2]
    )
    # _____008_1.Value -> compare_001.B
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Compare.001"].inputs[3]
    )
    # ___002.分段4D -> ___003.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["切换.003"].inputs[0]
    )
    # ____009.Source FPS -> ___029.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.009"].outputs[9],
        ugrs_mainnodetree_v1_0_1.nodes["运算.029"].inputs[1]
    )
    # ___033.Value -> ___003.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.033"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.003"].inputs[2]
    )
    # ____005.Output -> ___003.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.003"].inputs[1]
    )
    # ___003.Output -> ___029.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.029"].inputs[0]
    )
    # ____008_1.Output -> ___032.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.032"].inputs[0]
    )
    # ___032.Value -> ___040.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.032"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.040"].inputs[0]
    )
    # ____007_1.Source FPS -> math_multiply_001.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.007"].outputs[9],
        ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply.001"].inputs[0]
    )
    # simulation_output.Current Frame -> math_multiply_001.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Simulation Output"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Math_Multiply.001"].inputs[1]
    )
    # ____008_1.Output -> ____005.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].inputs[0]
    )
    # ____005.Output -> ___033.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.033"].inputs[0]
    )
    # ____012.FrameCount -> ___032.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.012"].outputs[8],
        ugrs_mainnodetree_v1_0_1.nodes["运算.032"].inputs[1]
    )
    # ____012.FrameCount -> ___033.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.012"].outputs[8],
        ugrs_mainnodetree_v1_0_1.nodes["运算.033"].inputs[1]
    )
    # input_point_radius_012.Normalize -> ___004.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.012"].outputs[39],
        ugrs_mainnodetree_v1_0_1.nodes["切换.004"].inputs[0]
    )
    # _____014.Vector -> ___004.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.004"].inputs[2]
    )
    # ___xyz_004.Vector -> ___004.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.004"].inputs[1]
    )
    # ___xyz_004.Vector -> _____014.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.014"].inputs[0]
    )
    # ___004.Output -> _____012.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.012"].inputs[0]
    )
    # ______014.Attribute -> ___024.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.024"].inputs[0]
    )
    # ______012.Attribute -> ___041.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.012"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.041"].inputs[0]
    )
    # ______013.Attribute -> ___042.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.042"].inputs[0]
    )
    # ______004.Attribute -> ___003_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["群组.003"].inputs[0]
    )
    # ___024.Value -> ___xyz_002.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.024"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].inputs[0]
    )
    # ___041.Value -> ___xyz_002.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.041"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].inputs[1]
    )
    # ___024.Value -> ___008.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.024"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.008"].inputs[0]
    )
    # ___041.Value -> ___008.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.041"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.008"].inputs[1]
    )
    # input_point_radius_001.Point Radius -> ___035.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].outputs[10],
        ugrs_mainnodetree_v1_0_1.nodes["运算.035"].inputs[0]
    )
    # input_point_radius_001.Point Radius -> ___026.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].outputs[10],
        ugrs_mainnodetree_v1_0_1.nodes["运算.026"].inputs[1]
    )
    # ____006_1.Output -> ____010.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.010"].inputs[0]
    )
    # ____018.Output -> ____017.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.017"].inputs[0]
    )
    # ________010.Geometry -> ____018.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.018"].inputs[0]
    )
    # ___009.Value -> ___020.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.009"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.020"].inputs[0]
    )
    # ___020.Value -> ___026.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.020"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.026"].inputs[0]
    )
    # _____3.Value -> __________.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串"].inputs[0]
    )
    # __________.String -> ______1.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串"].inputs[1]
    )
    # ______1.String -> ______006.Name
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.006"].inputs[0]
    )
    # ____038.Output -> _____3.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算"].inputs[0]
    )
    # _____001_3.Value -> ___________001.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.001"].inputs[0]
    )
    # _____002_2.Value -> ___________002.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.002"].inputs[0]
    )
    # ______001.String -> ______007.Name
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.007"].inputs[0]
    )
    # ______002.String -> ______008.Name
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.008"].inputs[0]
    )
    # ___________001.String -> ______001.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.001"].inputs[1]
    )
    # ___________002.String -> ______002.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.002"].inputs[1]
    )
    # ____038.Output -> _____001_3.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.001"].inputs[0]
    )
    # ____038.Output -> _____002_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.002"].inputs[0]
    )
    # _____1.几何数据 -> ________021.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输入"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].inputs[0]
    )
    # _____004_1.Value -> ___________003.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.003"].inputs[0]
    )
    # ___________003.String -> ______003.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["数值 转换为 字符串.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.003"].inputs[1]
    )
    # ______003.String -> ________021.Name
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].inputs[2]
    )
    # ___xyz.Vector -> ________021.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].inputs[3]
    )
    # ________021.Geometry -> _____2.几何数据
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["重复输出"].inputs[0]
    )
    # ____1.String -> ____021.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["字符串"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].inputs[0]
    )
    # ______009.Attribute -> ___xyz_001.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.009"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].inputs[0]
    )
    # ______010.Attribute -> ___xyz_001.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].inputs[1]
    )
    # ______011.Attribute -> ___xyz_001.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.011"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].inputs[2]
    )
    # ___xyz_001.Vector -> ________022.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.022"].inputs[3]
    )
    # ________022.Geometry -> _____1.几何数据
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.022"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["重复输入"].inputs[1]
    )
    # ______019.Attribute -> ___xyz_003.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.019"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].inputs[0]
    )
    # ______020.Attribute -> ___xyz_003.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.020"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].inputs[1]
    )
    # ______021.Attribute -> ___xyz_003.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].inputs[2]
    )
    # ______025.Attribute -> ___xyz_004.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.025"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].inputs[0]
    )
    # ______026.Attribute -> ___xyz_004.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.026"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].inputs[1]
    )
    # ______027.Attribute -> ___xyz_004.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.027"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.004"].inputs[2]
    )
    # ______006.Attribute -> ___xyz.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].inputs[0]
    )
    # ______007.Attribute -> ___xyz.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].inputs[1]
    )
    # ______008.Attribute -> ___xyz.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ"].inputs[2]
    )
    # ___023.Value -> ___017.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.023"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.017"].inputs[1]
    )
    # _____003.Value -> ___036.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.003"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["运算.036"].inputs[0]
    )
    # ____003_1.Output -> ________022.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.022"].inputs[0]
    )
    # _____006_1.Rotation -> ________023.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.006"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.023"].inputs[3]
    )
    # ________023.Geometry -> ___006.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.023"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.006"].inputs[1]
    )
    # ___006.Output -> ____027.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.027"].inputs[0]
    )
    # ____027.Output -> _____003_1.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.027"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实现实例.003"].inputs[0]
    )
    # __.Output -> ____004.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.004"].inputs[0]
    )
    # ____044.Output -> ___010.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.010"].inputs[0]
    )
    # group_input_004.SRC Fm Start -> ___010.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Group Input.004"].outputs[15],
        ugrs_mainnodetree_v1_0_1.nodes["运算.010"].inputs[1]
    )
    # ___010.Value -> __.SRC_Fm
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["群组"].inputs[2]
    )
    # ____037.Output -> _____1.Iterations
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.037"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["重复输入"].inputs[0]
    )
    # ____039.Output -> ____036.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.039"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.036"].inputs[0]
    )
    # ____036.Output -> _____001_3.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.036"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.001"].inputs[1]
    )
    # ____036.Output -> ____037.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.036"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.037"].inputs[0]
    )
    # _____1.Iteration -> ____038.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输入"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.038"].inputs[0]
    )
    # input_point_radius_017.SHFormat -> _____003_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.017"].outputs[13],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.003"].inputs[0]
    )
    # _____003_2.Value -> _____005.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.005"].inputs[0]
    )
    # _____003_2.Value -> _____005.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.005"].inputs[1]
    )
    # _____005.Value -> _____006.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.006"].inputs[0]
    )
    # _____006.Value -> ____039.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.039"].inputs[0]
    )
    # _____007.Value -> _____002_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.002"].inputs[1]
    )
    # ____010.Output -> ___001_1.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.001"].inputs[0]
    )
    # ____039.Output -> _____007.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.039"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.007"].inputs[0]
    )
    # input_point_radius_018.OutputChannle -> _____001_2.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.018"].outputs[34],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[0]
    )
    # ____023.Output -> ___008_1.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.023"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.008"].inputs[1]
    )
    # ____003_1.Output -> ____022.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.022"].inputs[0]
    )
    # ________026.Geometry -> ____023.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.026"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.023"].inputs[0]
    )
    # _______.Geometry -> ___008_1.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["删除已命名属性"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.008"].inputs[2]
    )
    # input_point_radius_019.PointScale -> _____003_3.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.019"].outputs[27],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].inputs[0]
    )
    # _______001.Mesh -> _______005.Instance
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["设置着色平滑.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].inputs[2]
    )
    # ____041.Output -> _______005.Points
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.041"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].inputs[0]
    )
    # ____020.Output -> ____041.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.020"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.041"].inputs[0]
    )
    # ________028.Geometry -> ________029.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.028"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.029"].inputs[0]
    )
    # ________029.Geometry -> ________030.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.029"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.030"].inputs[0]
    )
    # ___xyz_005.Vector -> ________028.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.028"].inputs[3]
    )
    # ___xyz_007.Vector -> ________029.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.029"].inputs[3]
    )
    # ___xyz_008.Vector -> ________030.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.030"].inputs[3]
    )
    # ____013_1.Output -> _______005.Rotation
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].inputs[5]
    )
    # _____003_4.Matrix -> _____001_4.Matrix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转置矩阵.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].inputs[0]
    )
    # _____001_4.Column 1 Row 1 -> ___xyz_005.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].inputs[0]
    )
    # _____001_4.Column 1 Row 2 -> ___xyz_005.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].inputs[1]
    )
    # _____001_4.Column 1 Row 3 -> ___xyz_005.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.005"].inputs[2]
    )
    # _____001_4.Column 2 Row 1 -> ___xyz_007.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].inputs[0]
    )
    # _____001_4.Column 2 Row 2 -> ___xyz_007.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[5],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].inputs[1]
    )
    # _____001_4.Column 2 Row 3 -> ___xyz_007.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[6],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.007"].inputs[2]
    )
    # _____001_4.Column 3 Row 1 -> ___xyz_008.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[8],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].inputs[0]
    )
    # _____001_4.Column 3 Row 2 -> ___xyz_008.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[9],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].inputs[1]
    )
    # _____001_4.Column 3 Row 3 -> ___xyz_008.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离矩阵.001"].outputs[10],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.008"].inputs[2]
    )
    # ____002.Matrix -> _____003_4.Matrix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["逆矩阵.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转置矩阵.003"].inputs[0]
    )
    # ___xyz_1.X -> ___056.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.056"].inputs[0]
    )
    # ___xyz_1.Y -> ___056.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["运算.056"].inputs[1]
    )
    # ___056.Value -> ___057.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.056"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.057"].inputs[0]
    )
    # ___xyz_1.Z -> ___057.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["运算.057"].inputs[1]
    )
    # ____041.Output -> ____025.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.041"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.025"].inputs[0]
    )
    # ___059.Value -> ______007_1.Selection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.059"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.007"].inputs[1]
    )
    # ____026.Output -> ___059.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.059"].inputs[0]
    )
    # input_point_radius_020.PreAlphaClip_Value -> ___059.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.020"].outputs[26],
        ugrs_mainnodetree_v1_0_1.nodes["运算.059"].inputs[1]
    )
    # input_point_radius_021.ColorFormat -> _____004_3.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.021"].outputs[12],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.004"].inputs[0]
    )
    # _____004_3.Output -> ___008_1.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.008"].inputs[0]
    )
    # ____022.Output -> ________026.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.022"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.026"].inputs[0]
    )
    # ______032.Attribute -> ________026.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.032"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.026"].inputs[3]
    )
    # input_point_radius_022.ShaderMode -> _____005_1.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.022"].outputs[32],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.005"].inputs[0]
    )
    # ____002_1.inv_Opacity -> ___003_1.inv_Opacity
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.002"].outputs[11],
        ugrs_mainnodetree_v1_0_1.nodes["群组.003"].inputs[1]
    )
    # _____008.Vector -> _____009.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.009"].inputs[0]
    )
    # _____009.Vector -> _____003.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.009"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.003"].inputs[0]
    )
    # ______015.Attribute -> ___________002_1.W
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.015"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].inputs[0]
    )
    # ______016.Attribute -> ___________002_1.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.016"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].inputs[1]
    )
    # ______017.Attribute -> ___________002_1.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].inputs[2]
    )
    # ______018.Attribute -> ___________002_1.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].inputs[3]
    )
    # ____001_1.Mesh -> _____4.Mesh
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["立方体.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["对偶网格"].inputs[0]
    )
    # ____013.ClipOfffset -> _____008_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.013"].outputs[16],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].inputs[0]
    )
    # ___040.Value -> _____008_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.040"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.008"].inputs[1]
    )
    # ____014.Geo_Size -> ____051.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.014"].outputs[20],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.051"].inputs[0]
    )
    # ___002.Output -> ___006.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.006"].inputs[2]
    )
    # ___002.Output -> ________023.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.023"].inputs[0]
    )
    # ____001.3DGS -> collection_info.Collection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.001"].outputs[5],
        ugrs_mainnodetree_v1_0_1.nodes["Collection Info"].inputs[0]
    )
    # _____016.Vector -> _____017.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.016"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.017"].inputs[0]
    )
    # _____018.Vector -> _____042.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.042"].inputs[0]
    )
    # _____044.Vector -> _____045.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.044"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.045"].inputs[0]
    )
    # _____019.Vector -> _____043.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.019"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.043"].inputs[0]
    )
    # _____046.Vector -> _____047.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.046"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.047"].inputs[0]
    )
    # _____048.Vector -> _____049.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.048"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.049"].inputs[0]
    )
    # ___044.Value -> ___058.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.044"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.058"].inputs[0]
    )
    # ___058.Value -> ___061.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.058"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.061"].inputs[0]
    )
    # ___061.Value -> _____048.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.061"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.048"].inputs[3]
    )
    # _____050.Vector -> _____051.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.050"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.051"].inputs[0]
    )
    # _____052.Vector -> _____053.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.052"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.053"].inputs[0]
    )
    # ___062.Value -> _____052.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.062"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.052"].inputs[3]
    )
    # _____017.Vector -> _____020.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.020"].inputs[1]
    )
    # _____020.Vector -> _____054.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.020"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.054"].inputs[0]
    )
    # _____042.Vector -> _____054.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.042"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.054"].inputs[1]
    )
    # _____054.Vector -> _____021.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.054"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.021"].inputs[0]
    )
    # _____045.Vector -> _____021.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.045"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.021"].inputs[1]
    )
    # _____047.Vector -> _____055.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.047"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.055"].inputs[1]
    )
    # _____058.Vector -> _____057.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.058"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.057"].inputs[0]
    )
    # _____055.Vector -> _____058.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.055"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.058"].inputs[0]
    )
    # _____049.Vector -> _____058.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.049"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.058"].inputs[1]
    )
    # _____051.Vector -> _____057.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.051"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.057"].inputs[1]
    )
    # _____053.Vector -> _____059.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.053"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.059"].inputs[1]
    )
    # _____057.Vector -> _____059.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.057"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.059"].inputs[0]
    )
    # _____061.Vector -> _____062.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.061"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.062"].inputs[0]
    )
    # ___063.Value -> ___064.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.063"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.064"].inputs[0]
    )
    # ___064.Value -> ___065.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.064"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.065"].inputs[0]
    )
    # ___065.Value -> _____061.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.065"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.061"].inputs[3]
    )
    # _____063.Vector -> _____064.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.063"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.064"].inputs[0]
    )
    # ___066.Value -> _____063.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.066"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.063"].inputs[3]
    )
    # _____065.Vector -> _____066.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.065"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.066"].inputs[0]
    )
    # ___067.Value -> ___068.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.067"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.068"].inputs[0]
    )
    # ___068.Value -> ___069.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.068"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.069"].inputs[0]
    )
    # ___069.Value -> ___070.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.069"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.070"].inputs[0]
    )
    # ___070.Value -> _____065.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.070"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.065"].inputs[3]
    )
    # _____067.Vector -> _____068.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.067"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.068"].inputs[0]
    )
    # ___072.Value -> ___073.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.072"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.073"].inputs[0]
    )
    # ___071.Value -> ___072.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.071"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.072"].inputs[0]
    )
    # ___074.Value -> ___072.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.074"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.072"].inputs[1]
    )
    # ___075.Value -> ___073.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.075"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.073"].inputs[1]
    )
    # ___073.Value -> ___076.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.073"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.076"].inputs[0]
    )
    # ___076.Value -> _____067.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.076"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.067"].inputs[3]
    )
    # _____069.Vector -> _____070.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.069"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.070"].inputs[0]
    )
    # ___077.Value -> ___078.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.077"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.078"].inputs[0]
    )
    # ___078.Value -> ___079.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.078"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.079"].inputs[0]
    )
    # ___079.Value -> ___080.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.079"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.080"].inputs[0]
    )
    # ___080.Value -> _____069.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.080"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.069"].inputs[3]
    )
    # _____071.Vector -> _____072.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.071"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.072"].inputs[0]
    )
    # ___081.Value -> ___082.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.081"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.082"].inputs[0]
    )
    # ___082.Value -> _____071.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.082"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.071"].inputs[3]
    )
    # _____073.Vector -> _____074.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.073"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.074"].inputs[0]
    )
    # ___083.Value -> ___084.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.083"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.084"].inputs[0]
    )
    # ___085.Value -> ___083.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.085"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.083"].inputs[1]
    )
    # ___084.Value -> _____073.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.084"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.073"].inputs[3]
    )
    # _____078.Vector -> _____077.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.078"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.077"].inputs[0]
    )
    # _____075.Vector -> _____078.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.075"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.078"].inputs[0]
    )
    # _____077.Vector -> _____079.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.077"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.079"].inputs[0]
    )
    # _____064.Vector -> _____075.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.064"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.075"].inputs[1]
    )
    # _____066.Vector -> _____078.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.066"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.078"].inputs[1]
    )
    # _____068.Vector -> _____077.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.068"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.077"].inputs[1]
    )
    # _____080.Vector -> _____081.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.080"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.081"].inputs[0]
    )
    # _____070.Vector -> _____079.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.070"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.079"].inputs[1]
    )
    # _____079.Vector -> _____080.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.079"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.080"].inputs[0]
    )
    # _____072.Vector -> _____080.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.072"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.080"].inputs[1]
    )
    # _____074.Vector -> _____081.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.074"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.081"].inputs[1]
    )
    # ______028.Attribute -> _____011.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.028"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.011"].inputs[0]
    )
    # ______031.Attribute -> _____016.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.031"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.016"].inputs[0]
    )
    # ___004_1.Y -> _____016.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.004"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.016"].inputs[3]
    )
    # ___005.Z -> _____018.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.005"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.018"].inputs[3]
    )
    # ______033.Attribute -> _____018.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.033"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.018"].inputs[0]
    )
    # ___007_1.X -> _____044.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.044"].inputs[3]
    )
    # ______034.Attribute -> _____044.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.034"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.044"].inputs[0]
    )
    # ______035.Attribute -> _____019.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.035"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.019"].inputs[0]
    )
    # ______036.Attribute -> _____046.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.036"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.046"].inputs[0]
    )
    # ______037.Attribute -> _____048.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.037"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.048"].inputs[0]
    )
    # ___008_2.xy -> _____019.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.008"].outputs[6],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.019"].inputs[3]
    )
    # ___009_1.yz -> _____046.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.009"].outputs[7],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.046"].inputs[3]
    )
    # ___010_1.zz -> ___044.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.010"].outputs[5],
        ugrs_mainnodetree_v1_0_1.nodes["运算.044"].inputs[0]
    )
    # ___010_1.yy -> ___061.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.010"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.061"].inputs[1]
    )
    # ___010_1.xx -> ___058.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.010"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.058"].inputs[1]
    )
    # ___011.xz -> _____050.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.011"].outputs[8],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.050"].inputs[3]
    )
    # ______038.Attribute -> _____050.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.038"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.050"].inputs[0]
    )
    # ______039.Attribute -> _____052.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.039"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.052"].inputs[0]
    )
    # ___012_1.yy -> ___062.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.012"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.062"].inputs[1]
    )
    # ___012_1.xx -> ___062.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.012"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.062"].inputs[0]
    )
    # ______040.Attribute -> _____061.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.040"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.061"].inputs[0]
    )
    # ___013_1.Y -> ___065.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.013"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["运算.065"].inputs[1]
    )
    # ___013_1.xx -> ___063.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.013"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.063"].inputs[0]
    )
    # ___013_1.yy -> ___064.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.013"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.064"].inputs[1]
    )
    # ___014_1.Z -> ___066.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.014"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["运算.066"].inputs[0]
    )
    # ___014_1.xy -> ___066.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.014"].outputs[6],
        ugrs_mainnodetree_v1_0_1.nodes["运算.066"].inputs[1]
    )
    # ______041.Attribute -> _____063.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.041"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.063"].inputs[0]
    )
    # ___015_1.Y -> ___070.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.015"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["运算.070"].inputs[1]
    )
    # ___015_1.xx -> ___068.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.015"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.068"].inputs[1]
    )
    # ___015_1.yy -> ___069.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.015"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.069"].inputs[1]
    )
    # ___015_1.zz -> ___067.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.015"].outputs[5],
        ugrs_mainnodetree_v1_0_1.nodes["运算.067"].inputs[0]
    )
    # ______042.Attribute -> _____065.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.042"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.065"].inputs[0]
    )
    # ___016_1.zz -> ___071.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.016"].outputs[5],
        ugrs_mainnodetree_v1_0_1.nodes["运算.071"].inputs[0]
    )
    # ___016_1.xx -> ___074.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.016"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.074"].inputs[0]
    )
    # ___016_1.yy -> ___075.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.016"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.075"].inputs[0]
    )
    # ___016_1.Z -> ___076.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.016"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["运算.076"].inputs[1]
    )
    # ______043.Attribute -> _____067.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.043"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.067"].inputs[0]
    )
    # ______044.Attribute -> _____069.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.044"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.069"].inputs[0]
    )
    # ___017_1.X -> ___080.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.080"].inputs[1]
    )
    # ___017_1.zz -> ___077.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.017"].outputs[5],
        ugrs_mainnodetree_v1_0_1.nodes["运算.077"].inputs[0]
    )
    # ___017_1.xx -> ___078.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.017"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.078"].inputs[1]
    )
    # ___017_1.yy -> ___079.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.017"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.079"].inputs[1]
    )
    # ______045.Attribute -> _____071.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.045"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.071"].inputs[0]
    )
    # ______046.Attribute -> _____073.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.046"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.073"].inputs[0]
    )
    # ___018_1.Z -> ___082.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.018"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["运算.082"].inputs[1]
    )
    # ___018_1.xx -> ___081.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.018"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.081"].inputs[0]
    )
    # ___018_1.yy -> ___081.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.018"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.081"].inputs[1]
    )
    # ___019.X -> ___084.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.019"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.084"].inputs[1]
    )
    # ___019.xx -> ___083.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.019"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["运算.083"].inputs[0]
    )
    # ___019.yy -> ___085.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.019"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["运算.085"].inputs[0]
    )
    # input_point_radius_024.clipArea -> _____004_2.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.024"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.004"].inputs[0]
    )
    # input_point_radius_023.object_clip -> ___010_2.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.023"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["切换.010"].inputs[0]
    )
    # _____5.Self Object -> _____006_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["自身物体"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.006"].inputs[0]
    )
    # _____001_5.Self Object -> _____007_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["自身物体.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.007"].inputs[0]
    )
    # ____001_2.Output -> ___012.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.012"].inputs[0]
    )
    # ______023.Attribute -> ___012.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.023"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.012"].inputs[1]
    )
    # ___xyz_003.Vector -> _____010.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.010"].inputs[0]
    )
    # ____013_1.Output -> _____001_6.Rotation
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并变换.001"].inputs[1]
    )
    # _____003_5.Matrix -> ____002.Matrix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矩阵相乘.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["逆矩阵.002"].inputs[0]
    )
    # _____007_1.Transform -> _____003_5.Matrix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矩阵相乘.003"].inputs[0]
    )
    # _____001_6.Transform -> _____003_5.Matrix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并变换.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矩阵相乘.003"].inputs[1]
    )
    # ____3.Vector -> ________018.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["投影点"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.018"].inputs[3]
    )
    # ____016_1.Output -> _____001_6.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并变换.001"].inputs[2]
    )
    # ___007.Position -> _____008.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["位置.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.008"].inputs[0]
    )
    # _____004_2.Scale -> _____6.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.004"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["旋转矢量"].inputs[0]
    )
    # _____6.Vector -> _____009.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["旋转矢量"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.009"].inputs[1]
    )
    # _____004_2.Location -> _____008.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.004"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.008"].inputs[1]
    )
    # _____006_1.Rotation -> _____6.Rotation
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.006"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["旋转矢量"].inputs[1]
    )
    # _____002_3.Location -> _____022.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.002"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.022"].inputs[1]
    )
    # _____022.Vector -> _____7.Ray Direction
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.022"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["光线投射"].inputs[4]
    )
    # ____054.Output -> _____7.Source Position
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.054"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["光线投射"].inputs[3]
    )
    # ____054.Output -> _____022.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.054"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.022"].inputs[0]
    )
    # ___010_3.Position -> ____054.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["位置.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.054"].inputs[0]
    )
    # _____8.Boolean -> ______003_1.Selection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.003"].inputs[1]
    )
    # _____7.Is Hit -> _____8.Boolean
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["光线投射"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算"].inputs[0]
    )
    # _____002_3.Geometry -> _____7.Target Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.002"].outputs[4],
        ugrs_mainnodetree_v1_0_1.nodes["光线投射"].inputs[0]
    )
    # reroute.Output -> ______003_1.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Reroute"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.003"].inputs[0]
    )
    # reroute.Output -> ___010_2.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Reroute"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.010"].inputs[1]
    )
    # ______003_1.Geometry -> ___010_2.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.010"].inputs[2]
    )
    # ___010_2.Output -> ____003_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.003"].inputs[0]
    )
    # ____051.Output -> ___086.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.051"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.086"].inputs[0]
    )
    # ____4.Matrix -> ____001_4.Transform
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["逆矩阵"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["变换点.001"].inputs[1]
    )
    # _____008_2.Transform -> ____4.Matrix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["逆矩阵"].inputs[0]
    )
    # ____001_4.Vector -> ____001_5.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["变换点.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].inputs[0]
    )
    # camera_info.Projection Matrix -> ____001_5.Transform
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Camera Info"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].inputs[1]
    )
    # ____001_5.Vector -> _____001_7.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.001"].inputs[0]
    )
    # ____2.Output -> ______008_1.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.008"].inputs[0]
    )
    # _____002_4.Self Object -> _____009_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["自身物体.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.009"].inputs[0]
    )
    # _____009_1.Transform -> ____002_2.Transform
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.009"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点.002"].inputs[1]
    )
    # ___011_1.Position -> ____002_2.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["位置.011"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点.002"].inputs[0]
    )
    # ____002_2.Vector -> ____001_4.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["投影点.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["变换点.001"].inputs[0]
    )
    # ____5.view_clip -> ___012_2.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["切换.012"].inputs[0]
    )
    # ______008_1.Geometry -> ___012_2.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.012"].inputs[2]
    )
    # ____2.Output -> ___012_2.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.012"].inputs[1]
    )
    # ___008_1.Output -> ______007_1.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.007"].inputs[0]
    )
    # ____016_1.Output -> ___xyz_1.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ"].inputs[0]
    )
    # ____051.Output -> _____023.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.051"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.023"].inputs[3]
    )
    # ____016_1.Output -> _____023.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.023"].inputs[0]
    )
    # input_point_radius_026.Mesh -> _____006_2.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.026"].outputs[23],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].inputs[0]
    )
    # ____001_1.Mesh -> _____006_2.Cube
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["立方体.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].inputs[1]
    )
    # ___.Mesh -> _____006_2.IcoSphere
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["棱角球"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].inputs[2]
    )
    # _______005.Instances -> ____.Mesh
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].inputs[2]
    )
    # ___035.Value -> _____003_3.Fix
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.035"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].inputs[1]
    )
    # ___026.Value -> _____003_3.Auto
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.026"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].inputs[2]
    )
    # ___057.Value -> _____003_3.Max
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.057"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].inputs[3]
    )
    # _____003_3.Output -> ___086.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.086"].inputs[1]
    )
    # ____025.Output -> mesh_to_points_003.Mesh
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.025"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Mesh to Points.003"].inputs[0]
    )
    # mesh_to_points_003.Points -> ____.PointCloud
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Mesh to Points.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].inputs[1]
    )
    # ________030.Geometry -> ____020.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.030"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.020"].inputs[0]
    )
    # ___004_2.Position -> ____3.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["位置.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点"].inputs[0]
    )
    # _____2.几何数据 -> _______.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输出"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除已命名属性"].inputs[0]
    )
    # ______029.Attribute -> ___xyz_006.X
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.029"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].inputs[0]
    )
    # ______030.Attribute -> ___xyz_006.Y
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.030"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].inputs[1]
    )
    # ______047.Attribute -> ___xyz_006.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.047"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].inputs[2]
    )
    # ____011_1.Output -> _____001_2.Final color
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.011"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[1]
    )
    # _____032.Vector -> _____001_2.Albedo
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.032"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[5]
    )
    # ____015.Output -> _____032.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.015"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.032"].inputs[0]
    )
    # ____014_1.Output -> _____034.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.034"].inputs[0]
    )
    # input_point_radius_028.Normalize -> ___013_2.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.028"].outputs[39],
        ugrs_mainnodetree_v1_0_1.nodes["切换.013"].inputs[0]
    )
    # _____034.Vector -> ___013_2.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.034"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.013"].inputs[2]
    )
    # ___013_2.Output -> _____001_2.optical flows
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[2]
    )
    # input_point_radius_028.Length -> ___014_2.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.028"].outputs[38],
        ugrs_mainnodetree_v1_0_1.nodes["切换.014"].inputs[0]
    )
    # ____014_1.Output -> _____035.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.035"].inputs[0]
    )
    # _____035.Value -> ___014_2.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.035"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["切换.014"].inputs[2]
    )
    # ____014_1.Output -> ___014_2.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.014"].inputs[1]
    )
    # ___014_2.Output -> ___013_2.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.013"].inputs[1]
    )
    # input_point_radius_027.Precompute -> ___017_2.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.027"].outputs[33],
        ugrs_mainnodetree_v1_0_1.nodes["切换.017"].inputs[0]
    )
    # ____042.Output -> ___017_2.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.042"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.017"].inputs[1]
    )
    # ___xyz_003.Vector -> _____036.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.036"].inputs[0]
    )
    # _____036.Value -> ___028.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.036"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["运算.028"].inputs[0]
    )
    # ____028.Output -> _____10.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.028"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["元素排序"].inputs[0]
    )
    # ______001_1.Active Camera -> _____012_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.012"].inputs[0]
    )
    # ___005_1.Position -> _____037.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["位置.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.037"].inputs[0]
    )
    # _____012_1.Location -> _____037.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.012"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.037"].inputs[1]
    )
    # ___001_2.Value -> _____10.Sort Weight
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["元素排序"].inputs[3]
    )
    # ____029.Output -> ___xyz_002_1.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.029"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.002"].inputs[0]
    )
    # ______007_1.Geometry -> ___002_2.几何数据
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["烘焙.002"].inputs[0]
    )
    # ____045.Output -> ______010_1.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.045"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.010"].inputs[0]
    )
    # ______010_1.Geometry -> _____001.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["设置位置.001"].inputs[0]
    )
    # _____001.Geometry -> ___001_1.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["设置位置.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.001"].inputs[2]
    )
    # ___060.Value -> ___087.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.060"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.087"].inputs[0]
    )
    # ___087.Value -> ___088.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.087"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.088"].inputs[0]
    )
    # ______001_2.Attribute -> ___060.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.060"].inputs[0]
    )
    # ___088.Value -> ___094.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.088"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.094"].inputs[1]
    )
    # ___094.Value -> ___095.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.094"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.095"].inputs[0]
    )
    # ___095.Value -> _____001_2.t_scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.095"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[8]
    )
    # ____045.Output -> ___001_1.False
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.045"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.001"].inputs[1]
    )
    # _____11.Curve -> _____004_4.Curve
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["曲线圆环"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["填充曲线.004"].inputs[0]
    )
    # ___042.Value -> ___018_2.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.042"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.018"].inputs[2]
    )
    # ___018_2.Output -> ___xyz_002.Z
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].inputs[2]
    )
    # _____006_2.Output -> _____007_2.3DGS
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].inputs[1]
    )
    # _____004_4.Mesh -> _____007_2.2DGS
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["填充曲线.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].inputs[2]
    )
    # _____007_2.Output -> _______001.Mesh
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["设置着色平滑.001"].inputs[0]
    )
    # ____004_1.GaussionMode -> _____007_2.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.004"].outputs[22],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.007"].inputs[0]
    )
    # ____004_1.edges -> _____11.Resolution
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.004"].outputs[24],
        ugrs_mainnodetree_v1_0_1.nodes["曲线圆环"].inputs[0]
    )
    # ______013.Exists -> ___018_2.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.013"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["切换.018"].inputs[0]
    )
    # ___018_2.Output -> ___009.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.009"].inputs[1]
    )
    # ____015.Output -> _____12.0
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.015"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["编号切换"].inputs[1]
    )
    # ___003_1.Value -> ____026.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].inputs[0]
    )
    # ___014.Value -> ___015.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.015"].inputs[0]
    )
    # ___015.Value -> ___016.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.015"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.016"].inputs[0]
    )
    # ___016.Value -> ___017.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.016"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.017"].inputs[0]
    )
    # ____029.Output -> ___xyz_003_1.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.029"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.003"].inputs[0]
    )
    # ____001_5.Vector -> ____029.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["投影点.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.029"].inputs[0]
    )
    # ___020_1.Vector -> _____001_2.Derict
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["群组.020"].outputs[9],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[7]
    )
    # _____004_5.Self Object -> _____013_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["自身物体.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.013"].inputs[0]
    )
    # _____10.Geometry -> ________028.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["元素排序"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.028"].inputs[0]
    )
    # _____013_1.Transform -> ____3.Transform
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点"].inputs[1]
    )
    # ________018.Geometry -> ____042.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.042"].inputs[0]
    )
    # _____043.Vector -> _____055.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.043"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.055"].inputs[0]
    )
    # _____062.Vector -> _____075.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.062"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.075"].inputs[0]
    )
    # _____084.Vector -> _____001_9.几何数据
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.084"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["重复输出.001"].inputs[0]
    )
    # _____021.Vector -> _____12.1
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["编号切换"].inputs[2]
    )
    # _____059.Vector -> _____12.2
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.059"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["编号切换"].inputs[3]
    )
    # _____081.Vector -> _____12.3
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.081"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["编号切换"].inputs[4]
    )
    # ____016.SH_end -> _____010_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.016"].outputs[36],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.010"].inputs[0]
    )
    # ____010_1.SH_start -> _____010_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.010"].outputs[35],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.010"].inputs[1]
    )
    # _____010_1.Value -> _____011_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.011"].inputs[0]
    )
    # _____011_1.Value -> _____001_8.Iterations
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.011"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["重复输入.001"].inputs[0]
    )
    # _____001_8.几何数据 -> _____084.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输入.001"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.084"].inputs[0]
    )
    # _____12.Output -> _____084.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["编号切换"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.084"].inputs[1]
    )
    # _____001_8.Iteration -> _____012_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输入.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.012"].inputs[1]
    )
    # ____010_1.SH_start -> _____012_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.010"].outputs[35],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.012"].inputs[0]
    )
    # _____012_2.Value -> _____12.Index
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.012"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["编号切换"].inputs[0]
    )
    # ____019.Output -> ____2.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.019"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点"].inputs[0]
    )
    # ___012_2.Output -> ________020.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.012"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.020"].inputs[0]
    )
    # ________020.Geometry -> ________018.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.020"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.018"].inputs[0]
    )
    # ____017.Output -> ____019.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.019"].inputs[0]
    )
    # ____026.Output -> _____002_1.Only Opacity
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.026"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].inputs[3]
    )
    # ___018.Value -> _____002_1.Only Marginal
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].inputs[2]
    )
    # ___039.Value -> _____002_1.Opacity & Marginal
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.039"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].inputs[1]
    )
    # input_point_radius_006.PreAlphaClip_Value -> ___089.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.006"].outputs[26],
        ugrs_mainnodetree_v1_0_1.nodes["运算.089"].inputs[1]
    )
    # _____002_1.Output -> ___089.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.089"].inputs[0]
    )
    # ___089.Value -> ______010_1.Selection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.089"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.010"].inputs[1]
    )
    # ___039.Value -> ________020.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.039"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.020"].inputs[3]
    )
    # ___xyz_002_1.Z -> ___001_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.002"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["运算.001"].inputs[0]
    )
    # ___________002_1.Rotation -> ____013_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["四元数 转换为 旋转.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.013"].inputs[0]
    )
    # _____4.Dual Mesh -> ______001_3.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["对偶网格"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["变换几何体.001"].inputs[0]
    )
    # ______001_3.Geometry -> _____006_2.DualIcoSphere
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["变换几何体.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.006"].inputs[3]
    )
    # ___xyz_004_1.X -> ___007_2.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.007"].inputs[0]
    )
    # ___xyz_004_1.Y -> ___019_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["运算.019"].inputs[0]
    )
    # ___xyz_004_1.Z -> ___030.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["运算.030"].inputs[0]
    )
    # ___007_2.Value -> _____004_6.Boolean
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算.004"].inputs[0]
    )
    # ___019_1.Value -> _____004_6.Boolean
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.019"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算.004"].inputs[1]
    )
    # ___030.Value -> _____005_2.Boolean
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.030"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算.005"].inputs[1]
    )
    # _____004_6.Boolean -> _____005_2.Boolean
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算.005"].inputs[0]
    )
    # _____001_7.Vector -> ___xyz_004_1.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.004"].inputs[0]
    )
    # _____005_2.Boolean -> ______008_1.Selection
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["布尔运算.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["删除几何体.008"].inputs[1]
    )
    # _____005_1.Output -> ________010.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.010"].inputs[3]
    )
    # ______003_2.Active Camera -> camera_info.Camera
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Camera Info"].inputs[0]
    )
    # ______004_1.Active Camera -> _____008_2.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.008"].inputs[0]
    )
    # _____005_3.Self Object -> _____014_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["自身物体.005"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.014"].inputs[0]
    )
    # ___xyz_006.Vector -> _____13.Direction
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["变换方向"].inputs[0]
    )
    # _____014_1.Transform -> _____13.Transform
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.014"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["变换方向"].inputs[1]
    )
    # _____13.Direction -> ____014_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["变换方向"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.014"].inputs[0]
    )
    # input_point_radius_024.clipArea -> _____002_3.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.024"].outputs[3],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.002"].inputs[0]
    )
    # _____011.Vector -> ____015.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.011"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.015"].inputs[0]
    )
    # _____085.Vector -> _____086.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.085"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.086"].inputs[0]
    )
    # _____013.Vector -> ____016_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.016"].inputs[0]
    )
    # _____039.Vector -> _____001_2.Normal
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.039"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[3]
    )
    # _____033.Vector -> _____039.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.033"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.039"].inputs[0]
    )
    # _____008_3.Self Object -> _____018_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["自身物体.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.018"].inputs[0]
    )
    # ______007_2.Active Camera -> _____019_1.Object
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["活动摄像机.007"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.019"].inputs[0]
    )
    # _____018_1.Transform -> ____006_2.Transform
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.018"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点.006"].inputs[1]
    )
    # _____019_1.Location -> _____040.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["物体信息.019"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.040"].inputs[1]
    )
    # ___006_1.Position -> ____006_2.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["位置.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["投影点.006"].inputs[0]
    )
    # ____006_2.Vector -> _____040.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["投影点.006"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.040"].inputs[0]
    )
    # _____040.Vector -> _____027.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.040"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].inputs[2]
    )
    # ______055.Attribute -> _____027.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.055"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].inputs[0]
    )
    # ______055.Attribute -> _____027.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.055"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].inputs[1]
    )
    # _____027.Vector -> _____033.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.027"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.033"].inputs[0]
    )
    # _____086.Vector -> _____008_4.Off
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.086"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].inputs[1]
    )
    # ____017_1.HDR -> _____008_4.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["组输入.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].inputs[0]
    )
    # ___017_2.Output -> ____028.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.017"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.028"].inputs[0]
    )
    # ____042.Output -> ________032.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.042"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.032"].inputs[0]
    )
    # ________032.Geometry -> ___017_2.True
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.032"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["切换.017"].inputs[2]
    )
    # group_input.Frame_Index_input -> ___100.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Group Input"].outputs[19],
        ugrs_mainnodetree_v1_0_1.nodes["运算.100"].inputs[0]
    )
    # group_input.Offset -> ___100.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Group Input"].outputs[18],
        ugrs_mainnodetree_v1_0_1.nodes["运算.100"].inputs[1]
    )
    # group_input.FrameOffset -> _____009_2.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Group Input"].outputs[17],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].inputs[0]
    )
    # ___100.Value -> _____009_2.On
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.100"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].inputs[2]
    )
    # group_input.Frame_Index_input -> _____009_2.Off
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["Group Input"].outputs[19],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].inputs[1]
    )
    # _____009_2.Output -> ____044.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.009"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.044"].inputs[0]
    )
    # ___002_2.几何数据 -> ____045.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["烘焙.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.045"].inputs[0]
    )
    # ___001_1.Output -> ________010.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["切换.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.010"].inputs[0]
    )
    # _____001_9.几何数据 -> ____011_1.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输出.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["转接点.011"].inputs[0]
    )
    # _____001_2.Output -> _____085.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.085"].inputs[0]
    )
    # _____001_2.Output -> _____008_4.On
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].inputs[2]
    )
    # _____008_4.Output -> ________032.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.008"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["存储已命名属性.032"].inputs[3]
    )
    # ___xyz_003_1.Z -> _____010_2.NDC
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["分离 XYZ.003"].outputs[2],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].inputs[1]
    )
    # input_point_radius_029.Mode -> _____010_2.Menu
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.029"].outputs[37],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].inputs[0]
    )
    # _____037.Value -> _____010_2.WORD
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.037"].outputs[1],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].inputs[2]
    )
    # _____010_2.Output -> _____001_2.depth
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.010"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[4]
    )
    # ______003_3.Attribute -> _____001_2.Alphac hannel
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["已命名属性.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换.001"].inputs[6]
    )
    # _____9.Geometry -> ____6.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["设置材质"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["组输出"].inputs[0]
    )
    # _____004.Geometry -> _____9.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["实现实例.004"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["设置材质"].inputs[0]
    )
    # ____.Output -> _____004.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["菜单切换"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实现实例.004"].inputs[0]
    )
    # _____003_1.Geometry -> reroute.Input
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["实现实例.003"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Reroute"].inputs[0]
    )
    # ___013.Value -> ___023.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.013"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["运算.023"].inputs[0]
    )
    # input_point_radius_001.Point Radius -> _____013.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.001"].outputs[10],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].inputs[3]
    )
    # _____023.Vector -> _______005.Scale
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.023"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["实例化于点上.005"].inputs[6]
    )
    # ___086.Value -> mesh_to_points_003.Radius
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["运算.086"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["Mesh to Points.003"].inputs[3]
    )
    # ___xyz_002.Vector -> _____015.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["合并 XYZ.002"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.015"].inputs[0]
    )
    # _____015.Vector -> _____013.Vector
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.015"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["矢量运算.013"].inputs[0]
    )
    # _____.Geometry -> _____002.Geometry
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["变换几何体"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并几何.002"].inputs[0]
    )
    # ____021.Output -> ______1.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串"].inputs[1]
    )
    # ____021.Output -> ______001.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.001"].inputs[1]
    )
    # ____021.Output -> ______002.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["转接点.021"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.002"].inputs[1]
    )
    # ____001_3.String -> ______003.Strings
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["字符串.001"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["合并字符串.003"].inputs[1]
    )
    # input_point_radius_007.mirrow -> ___002_1.Switch
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["input_point_radius.007"].outputs[28],
        ugrs_mainnodetree_v1_0_1.nodes["切换.002"].inputs[0]
    )
    # _____1.Iteration -> _____004_1.Value
    ugrs_mainnodetree_v1_0_1.links.new(
        ugrs_mainnodetree_v1_0_1.nodes["重复输入"].outputs[0],
        ugrs_mainnodetree_v1_0_1.nodes["整数运算.004"].inputs[0]
    )
    hdr_socket.default_value = 'On'
    input_format_socket.default_value = 'multi-4dgs'
    colorformat_socket.default_value = 'SH'
    control_method_socket.default_value = 'Frame Index'
    display_mode_socket.default_value = 'PointCloud'
    gaussionmode_socket.default_value = '3DGS'
    mesh_socket.default_value = 'IcoSphere'
    alphaclipmode_socket.default_value = 'Opacity & Marginal'
    pointscale_socket.default_value = 'Max'
    shadermode_socket.default_value = 'Gaussion'
    outputchannle_socket.default_value = 'Final color'
    mode_socket.default_value = 'NDC'

    return ugrs_mainnodetree_v1_0_1


if __name__ == "__main__":
    # Maps node tree creation functions to the node tree 
    # name, such that we don't recreate node trees unnecessarily
    node_tree_names : dict[typing.Callable, str] = {}

    menu_switching = menu_switching_1_node_group(node_tree_names)
    node_tree_names[menu_switching_1_node_group] = menu_switching.name

    input_method = input_method_1_node_group(node_tree_names)
    node_tree_names[input_method_1_node_group] = input_method.name

    sigmod_g = sigmod_g_1_node_group(node_tree_names)
    node_tree_names[sigmod_g_1_node_group] = sigmod_g.name

    sh_g = sh_g_1_node_group(node_tree_names)
    node_tree_names[sh_g_1_node_group] = sh_g.name

    ugrs_mainnodetree_v1_0 = ugrs_mainnodetree_v1_0_1_node_group(node_tree_names)
    node_tree_names[ugrs_mainnodetree_v1_0_1_node_group] = ugrs_mainnodetree_v1_0.name

