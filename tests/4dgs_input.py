import bpy
import mathutils
import os
import typing


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


if __name__ == "__main__":
    # Maps node tree creation functions to the node tree 
    # name, such that we don't recreate node trees unnecessarily
    node_tree_names : dict[typing.Callable, str] = {}

    input_method = input_method_1_node_group(node_tree_names)
    node_tree_names[input_method_1_node_group] = input_method.name

