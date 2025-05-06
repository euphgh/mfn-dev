from xml.etree.ElementTree import Element
from xml.etree import ElementTree as ET

# 命名空间映射
namespaces = {
    "ipxact": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
    "amd": "http://www.amd.com/XMLSchema/SPIRIT/1685-2021/Extensions",
}

# 注册命名空间（保存时保留前缀）
for prefix, uri in namespaces.items():
    ET.register_namespace(prefix, uri)


def remove_tag_recursive(parent: Element, tag_to_remove: str):
    """递归删除指定 tag"""
    # 复制子节点列表，避免遍历过程中修改导致问题
    for child in list(parent):
        # 如果 tag 匹配，删除它
        if child.tag == tag_to_remove:
            parent.remove(child)
        else:
            remove_tag_recursive(child, tag_to_remove)


# 加载 XML 文件
tree = ET.parse("component.xml")
root = tree.getroot()

tag_list = [
    "designInstantiationRef",
    "designConfigurationInstantiationRef",
    "designInstantiation",
    "designConfigurationInstantiation",
]

for tag in tag_list:
    tag_to_remove = f"{{{namespaces['ipxact']}}}{tag}"
    remove_tag_recursive(root, tag_to_remove)

# 保存修改后的 XML
tree.write("leaf.xml", encoding="utf-8", xml_declaration=True)
