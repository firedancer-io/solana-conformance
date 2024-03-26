cimport superbased58

# Constants for buffer sizes including null terminator
cpdef encode_32(bytes data):
    cdef char out_buffer[45]
    cdef unsigned long length = 0
    cdef char* result = superbased58.fd_base58_encode_32(<unsigned char*> data, &length, out_buffer)
    if result == NULL:
        raise MemoryError("Failed to encode data.")
    return out_buffer[:length]

cpdef encode_64(bytes data):
    cdef char out_buffer[89]
    cdef unsigned long length = 0
    cdef char* result = superbased58.fd_base58_encode_64(<unsigned char*> data, &length, out_buffer)
    if result == NULL:
        raise MemoryError("Failed to encode data.")
    return out_buffer[:length]

cpdef decode_32(bytes encoded):
    cdef unsigned char out_buffer[32]
    cdef unsigned char* result = superbased58.fd_base58_decode_32(<const char*>encoded, out_buffer)
    if result == NULL:
        raise ValueError("Failed to decode data.")
    return bytes(out_buffer)

cpdef decode_64(bytes encoded):
    cdef unsigned char out_buffer[64]
    cdef unsigned char* result = superbased58.fd_base58_decode_64(<const char*>encoded, out_buffer)
    if result == NULL:
        raise ValueError("Failed to decode data.")
    return bytes(out_buffer)
