# superbased58.pxd
cdef extern from "fd_base58.h":
    char* fd_base58_encode_32(const unsigned char* bytes, unsigned long* opt_len, char* out)
    char* fd_base58_encode_64(const unsigned char* bytes, unsigned long* opt_len, char* out)
    unsigned char* fd_base58_decode_32(const char* encoded, unsigned char* out)
    unsigned char* fd_base58_decode_64(const char* encoded, unsigned char* out)
