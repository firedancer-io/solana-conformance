cimport superbased58

# Constants for buffer sizes including null terminator
cpdef encode_32(bytes data):
    cdef char[45] out_buffer
    cdef unsigned long length = 0
    cdef char* result = superbased58.fd_base58_encode_32(<unsigned char*> data, &length, out_buffer)
    if result == NULL:
        raise MemoryError("Failed to encode data.")
    return out_buffer[:length]

cpdef encode_64(bytes data):
    cdef char[89] out_buffer
    cdef unsigned long length = 0
    cdef char* result = superbased58.fd_base58_encode_64(<unsigned char*> data, &length, out_buffer)
    if result == NULL:
        raise MemoryError("Failed to encode data.")
    return out_buffer[:length]

cpdef decode_32(bytes encoded):
    cdef unsigned char[32] out_buffer
    cdef unsigned char* result = superbased58.fd_base58_decode_32(<const char*>encoded, out_buffer)
    if result == NULL:
        raise ValueError("Failed to decode data.")
    return out_buffer[:32]

cpdef decode_64(bytes encoded):
    cdef unsigned char[64] out_buffer
    cdef unsigned char* result = superbased58.fd_base58_decode_64(<const char*>encoded, out_buffer)
    if result == NULL:
        raise ValueError("Failed to decode data.")
    return out_buffer[:64]
