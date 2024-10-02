from google.protobuf.descriptor import Descriptor
from google.protobuf.message import Message


def find_field_with_type(
    descriptor: Descriptor, target_descriptor: Descriptor
) -> list[list[str]]:
    """
    Recursively searches for a field in the given descriptor that matches the target descriptor.

    :param descriptor: The descriptor of the protobuf message being searched.
    :param target_descriptor: The descriptor of the type we are looking for.
    :return: A list of field paths that match the target type.
    """
    matches = []

    def search_fields(descriptor, current_path):
        for field in descriptor.fields:
            if field.message_type == target_descriptor:
                matches.append(current_path + [field.name])
            elif field.type == field.TYPE_MESSAGE:
                search_fields(field.message_type, current_path + [field.name])

    search_fields(descriptor, [])
    return matches


def access_nested_field_safe(message: Message, field_path: list[str]):
    """
    Safely accesses a nested field in a protobuf message.

    :param message: The protobuf message instance.
    :param field_path: List of field names to reach the desired field.
    :return: The value of the nested field or None if any field in the path doesn't exist.
    """
    current_value = message
    for field_name in field_path:
        if current_value.HasField(field_name):
            current_value = getattr(current_value, field_name)
        else:
            return (
                None  # Field doesn't exist, return None or handle the case accordingly
            )
    return current_value
