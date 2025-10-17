import base64
import hashlib
import test_suite.protos.vm_pb2 as vm_pb

OUTPUT_DIR = "./test-vectors/syscall/tests/alt_bn128"
HEAP_START = 0x300000000
CU_BASE = 542
CU_PER_ELEM = 61
CU_MEM_OP = 10

ADD_OP = 0
ADD_SZ = 64 + 64
ADD_CU = 334

MUL_OP = 2
MUL_SZ = 64 + 32
MUL_CU = 3840

PAIRING_OP = 3
PAIRING_SZ = (64 + 128) * 2
PAIRING_CU = 36364 + 12121 + PAIRING_SZ + 85 + 32  # wtf!?

COMP_G1_OP = 0
COMP_G1_SZ = 64
COMP_G1_CU = 30 + 100

DECOMP_G1_OP = 1
DECOMP_G1_SZ = 32
DECOMP_G1_CU = 398 + 100

COMP_G2_OP = 2
COMP_G2_SZ = 128
COMP_G2_CU = 86 + 100

DECOMP_G2_OP = 3
DECOMP_G2_SZ = 64
DECOMP_G2_CU = 13610 + 100

# Sage script
#
# def xprint(name, val):
#     print(name+"\t= \""+val.hex().rjust(64, "0")+"\"")
#
# p=0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47
# r=0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
# f=Mod(0x3fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, p)
# half_p_plus1 = Mod((p+1)//2, p)
# half_p_neg1 = Mod((p-1)//2, p)
#
# xprint("r", r)
# xprint("r_plus1", r+1)
# xprint("r_neg1", r-1)
# xprint("half_r_plus1", lift(Mod((r+1)//2, r)))
# xprint("half_r_neg1", lift(Mod((r-1)//2, r)))
# xprint("ff", 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
# xprint("p", p)
# xprint("p_plus1", p+1)
# xprint("half_p_plus1", lift(half_p_plus1))
# xprint("half_p_neg1", lift(half_p_neg1))
# xprint("zero", 0)
# xprint("one", 1)
# xprint("two", 2)
# xprint("sqrt_2", lift(sqrt(Mod(2, p))))
# xprint("sqrt_11", lift(sqrt(Mod(11, p))))
# xprint("cbrt_neg2", lift(Mod(-2, p).nth_root(3)))
# xprint("neg_one", lift(Mod(-1,p)))
# xprint("neg_two", lift(Mod(-2,p)))
# xprint("neg_sqrt_2", lift(-sqrt(Mod(2, p))))
# xprint("neg_sqrt_11", lift(-sqrt(Mod(11, p))))
# xprint("neg_cbrt_neg2", lift(-Mod(-2, p).nth_root(3)))
# xprint("y_of_half_p_plus1", lift(sqrt(half_p_plus1^3+3)))
# xprint("neg_y_of_half_p_plus1", lift(-sqrt(half_p_plus1^3+3)))
# xprint("y_of_half_p_neg1", lift(sqrt(half_p_neg1^3+3)))
# xprint("neg_y_of_half_p_neg1", lift(-sqrt(half_p_neg1^3+3)))

# annoying values
r = "30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001"
r_plus1 = "30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000002"
r_neg1 = "30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000"
half_r_plus1 = "183227397098d014dc2822db40c0ac2e9419f4243cdcb848a1f0fac9f8000001"
half_r_neg1 = "183227397098d014dc2822db40c0ac2e9419f4243cdcb848a1f0fac9f8000000"
ff = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
three_f = "3fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
p = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47"
p_plus1 = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd48"
p_plus2 = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd49"
p_plus4 = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd4b"
half_p_plus1 = "183227397098d014dc2822db40c0ac2ecbc0b548b438e5469e10460b6c3e7ea4"
half_p_neg1 = "183227397098d014dc2822db40c0ac2ecbc0b548b438e5469e10460b6c3e7ea3"
zero = "0000000000000000000000000000000000000000000000000000000000000000"
one = "0000000000000000000000000000000000000000000000000000000000000001"
two = "0000000000000000000000000000000000000000000000000000000000000002"
four = "0000000000000000000000000000000000000000000000000000000000000004"
sqrt_2 = "08c6d2adffacbc8438f09f321874ea66e2fcc29f8dcfec2caefa21ec8c96a408"
sqrt_11 = "0ce2c194b86251806451ec04be095d60517130cff61fcb49c4ef4e708dac7f34"
cbrt_neg2 = "2409ed9a7b7567337c6bfd3b97e9703c9deffb228c6c7324d8a447837238b15e"
neg_one = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd46"
neg_two = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd45"
neg_four = "30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd43"
neg_sqrt_2 = "279d7bc4e184e3a57f5fa684690c6df6b484a7f1daa1de608d266a2a4be6593f"
neg_sqrt_11 = "23818cde28cf4ea953fe59b1c377fafd461039c17251ff4377313da64ad07e13"
neg_cbrt_neg2 = "0c5a60d865bc38f63be4487ae997e820f9916f6edc055768637c449366444be9"
y_of_half_p_plus1 = "0af887597f97eba5472cc6fe9e9225009bbbf3477143e737dab8aa67afbc4d0a"
neg_y_of_half_p_plus1 = (
    "256bc7196199b48471237eb7e2ef335cfbc57749f72de3556167e1af28c0b03d"
)
y_of_half_p_neg1 = "0a6ea289876b139cfe2cd1f08c065a2ab4aad542eaccb013520ea36934e877b4"
neg_y_of_half_p_neg1 = (
    "25f5abe959c68c8cba2373c5f57afe32e2d6954e7da51a79ea11e8ada3948593"
)
threef_mod_p = "0f9bb18d1ece5fd647afba497e7ea7a2687e956e978e3572c3df73e9278302b8"
y_of_threef = "050627a03f77e36ba8541ff3e600a32a4792560aeb37454c810120db7063b653"
neg_y_of_threef = "2b5e26d2a1b9bcbe0ffc25c29b80b5334fef14867d3a8540bb1f6b3b681946f4"
x_of_p_plus1_half = "113568bcb08769c966ff32fc8d27c3d0bbaf342cdc318bddcbd287f8a5b99a52"
p_plus1_half = "183227397098d014dc2822db40c0ac2ecbc0b548b438e5469e10460b6c3e7ea4"
neg_p_plus1_half = "183227397098d014dc2822db40c0ac2ecbc0b548b438e5469e10460b6c3e7ea3"

annoying_scalars = [
    # valid
    zero,
    one,
    r_neg1,
    half_r_neg1,
    half_r_plus1,
    # invalid (though accepted)
    r,
    r_plus1,
    three_f,
    ff,
]
annoying_scalars = [base64.b16decode(scalar, True) for scalar in annoying_scalars]

annoying_points = [
    # there's no point with x=0 or y=0
    # valid
    [zero, zero],  # point at infinity
    [one, two],
    [one, neg_two],
    [neg_one, sqrt_2],
    [neg_one, neg_sqrt_2],
    [two, sqrt_11],
    [two, neg_sqrt_11],
    [cbrt_neg2, one],
    [cbrt_neg2, neg_one],
    [half_p_plus1, y_of_half_p_plus1],
    [half_p_plus1, neg_y_of_half_p_plus1],
    [half_p_neg1, y_of_half_p_neg1],
    [half_p_neg1, neg_y_of_half_p_neg1],
    [threef_mod_p, y_of_threef],
    [threef_mod_p, neg_y_of_threef],
    [
        x_of_p_plus1_half,
        p_plus1_half,
    ],  # this is annoying because sqrt(.) = (p+1)/2 which is exactly at the cut off of neg vs pos
    [x_of_p_plus1_half, neg_p_plus1_half],
    # invalid
    [p_plus1, neg_two],  # invalid x>=p
    [p_plus2, sqrt_11],  # invalid x>=p
    [three_f, y_of_threef],  # invalid x>=p
    [three_f, neg_y_of_threef],  # invalid x>=p
    [one, p_plus2],  # invalid y>=p
    [cbrt_neg2, p_plus1],  # invalid y>=p
    [p, one],  # invalid x>=p + not on curve
    [one, p],  # invalid y>=p + not on curve
    [zero, one],  # not on curve
    [one, zero],  # not on curve
    [two, one],  # not on curve
]
annoying_points = [
    [base64.b16decode(coord, True) for coord in point] for point in annoying_points
]

very_annoying_points = [point for point in annoying_points]
for point in annoying_points:
    x = point[0]
    y = point[1]
    very_annoying_points.append([bytes([x[0] | 0x80]) + x[1:], y])
    very_annoying_points.append([bytes([x[0] | 0x40]) + x[1:], y])
    very_annoying_points.append([bytes([x[0] | 0xC0]) + x[1:], y])
    very_annoying_points.append([x, bytes([y[0] | 0x80]) + y[1:]])
    very_annoying_points.append([x, bytes([y[0] | 0x40]) + y[1:]])
    very_annoying_points.append([x, bytes([y[0] | 0xC0]) + y[1:]])

# def xprint2(name, val):
#     print(name+"\t= [\""+lift(val[0]).hex().rjust(64, "0")+"\",\n\t   \""+lift(val[1]).hex().rjust(64, "0")+"\"]")
#
# p = 0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd47
#
# k.<u>=GF(p^2)
# b = 3/(9+u)
# xprint2("b_prime", b)
#
# sqrt_b = sqrt(b)
# xprint2("sqrt_b_prime", sqrt_b)
# xprint2("neg_sqrt_of_b_prime", -sqrt_b)
# xprint2("x_of_1_neg_b_prime", (1-b).nth_root(3))
# sqrt_b_neg1 = sqrt(b-1)
# xprint2("sqrt_b_prime_neg1", sqrt_b_neg1)
# xprint2("sqrt_b_prime_neg1", -sqrt_b_neg1)
# sqrt_27_plus_b = sqrt(b+27)
# xprint2("sqrt_27_plus_b", sqrt_27_plus_b)
# xprint2("neg_sqrt_27_plus_b", -sqrt_27_plus_b)
#
# E = EllipticCurve(K, [0, b])
# P = E.random_point()
# r = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
# c = 21888242871839275222246405745257275088844257914179612981679871602714643921549
#
# Q = c*P
# print( r*P )
# xprint2("q_x", Q[0])
# xprint2("q_y", Q[1])
# xprint2("-q_y", -Q[1])
zero_fp2 = [zero, zero]
one_fp2 = [one, zero]
four_fp2 = [four, zero]
neg_one_fp2 = [neg_one, zero]
neg_four_fp2 = [neg_four, zero]
u_fp2 = [zero, one]
sqrt_b_plus1 = [
    "07fb3d558dafafb6bf6dd326a5fefe0beca3f9ac3bd999a390d504fad34b0b8c",
    "2351dcdda257b62181cbd745dfee16d5fdf4eb185bbcf33c20a0fe6eaa9cb4a3",
]
neg_sqrt_b_plus1 = [
    "2869111d5381f072f8e2728fdb825a51aadd70e52c9830e9ab4b871c0531f1bb",
    "0d1271953ed9ea0836846e70a1934187998c7f790cb4d7511b7f8da82de048a4",
]
sqrt_b_plus8 = [
    "181604d0560080401c08b557815482553e278257d98100d193a011c42782474d",
    "04f21f9d99cc25f694cf22ff70dc0ac4692e7a721b725dc454a217f04bd03e33",
]
neg_sqrt_b_plus8 = [
    "184e49a28b311fe99c47905f002cd6085959e8398ef0c9bba8807a52b0fab5fa",
    "2b722ed547657a33238122b710a54d992e52f01f4cff6cc8e77e74268cacbf14",
]
sqrt_b_plus_u3 = [
    "23712136978ed49faf2120ca4f7f71cfd4e7b46ffa0ea89edbc94ddc59238e9f",
    "28a7a81c6bf2a75dc9f0125bb581747e9e6b33fc3b2710a2309cef97a3163c65",
]
neg_sqrt_b_plus_u3 = [
    "0cf32d3c49a2cb8a092f24ec3201e68dc299b6216e6321ee60573e3a7f596ea8",
    "07bca656753ef8cbee60335acbffe3def91636952d4ab9eb0b839c7f3566c0e2",
]
x_of_4_neg_b = [
    "2546ace32139a7a3c69640d9df58e150b88a42c976cafdef331b58675f396376",
    "2994b43083ae5696b5cceb1ac5215caea04df0465b26971adc5ce02d0eb9cf1e",
]
p0_x = [
    "2596bb90715dfa4741dcbeaf28c320208deb53db69c03bdc77f94bfa8d9c5009",
    "149c5d10b3868d761097695617918ab5e34e0738d6599f2b819039699b0b67bd",
]
p0_y = [
    "090b286ef054afb53f78b704798292c0a34050335d9e5ffde8c44ccce1b7ce65",
    "017bcb12e82231f89202cad867962b32340b4fb0feac5c4a9b54e71818a4e995",
]
p0_neg_y = [
    "27592603f0dcf07478d78eb207fec59cf4411a5e0ad36a8f535c3f49f6c52ee2",
    "2ee8835ff90f6e31264d7ade19eb2d2b63761ae069c56e42a0cba4febfd813b2",
]
p1_x = [
    "2dfdbddb35cd04b9ce74a7a70a01cb33c68438b1f204f7eedb9cb04b80059a57",
    "195a872169329de142bed50d425185fbca9cb6a98705001a4ac22a88844146c5",
]
p1_y = [
    "24d32fefd984c28bfd9adf9fbc87b8e942127e8c65185f836bf305ac110f882f",
    "041122306036b204a1fbf64c80d523315dda91df56a9542308f4cd4a2ab178ed",
]
p1_neg_y = [
    "0b911e8307acdd9dbab56616c4f99f74556eec0503596b09d02d866ac76d7518",
    "2c532c4280faee2516544f6a00ac352c39a6d8b211c8766a332bbeccadcb845a",
]

annoying_points_g2 = [
    # there's no point with y=0
    # valid
    [zero_fp2, zero_fp2],  # point at infinity
    [p0_x, p0_y],  # y[0], y[1] have the same sign
    [p0_x, p0_neg_y],
    [p1_x, p1_y],  # y[0], y[1] have opposite signs
    [p1_x, p1_neg_y],
    # invalid
    [[p, zero], [zero, zero]],  # point at infinity - invalid x[0]>=p
    [[zero, p], [zero, zero]],  # point at infinity - invalid x[1]>=p
    [[zero, zero], [p, zero]],  # point at infinity - invalid y[0]>=p
    [[zero, zero], [zero, p]],  # point at infinity - invalid y[1]>=p
    [[p_plus1, zero], sqrt_b_plus1],  # invalid x[0]>=p
    [[one, p], sqrt_b_plus1],  # invalid x[1]>=p
    [x_of_4_neg_b, [p_plus4, zero]],  # invalid y[0]>=p
    [x_of_4_neg_b, [four, p]],  # invalid y[1]>=p
    [zero_fp2, one_fp2],  # not on curve (decompressed x to point at infinity)
    [one_fp2, zero_fp2],  # not on curve (can decompress x)
    [four_fp2, zero_fp2],  # not on curve (can't decompress x)
    [one_fp2, sqrt_b_plus1],  # on curve, not in group - y[0], y[1] have opposite signs
    [one_fp2, neg_sqrt_b_plus1],
    [u_fp2, sqrt_b_plus_u3],  # on curve, not in group - y[0], y[1] have the same sign
    [u_fp2, neg_sqrt_b_plus_u3],
]
annoying_points_g2 = [
    # coord[1] coord[0] because big endian
    [
        base64.b16decode(coord[1], True) + base64.b16decode(coord[0], True)
        for coord in point
    ]
    for point in annoying_points_g2
]
very_annoying_points_g2 = [point for point in annoying_points_g2]
for point in annoying_points_g2:
    x = point[0]
    y = point[1]
    very_annoying_points_g2.append([bytes([x[0] | 0x80]) + x[1:], y])
    very_annoying_points_g2.append([bytes([x[0] | 0x40]) + x[1:], y])
    very_annoying_points_g2.append([bytes([x[0] | 0xC0]) + x[1:], y])
    very_annoying_points_g2.append([x[:32] + bytes([x[32] | 0x80]) + x[33:], y])
    very_annoying_points_g2.append([x[:32] + bytes([x[32] | 0x40]) + x[33:], y])
    very_annoying_points_g2.append([x[:32] + bytes([x[32] | 0xC0]) + x[33:], y])
    very_annoying_points_g2.append([x, bytes([y[0] | 0x80]) + y[1:]])
    very_annoying_points_g2.append([x, bytes([y[0] | 0x40]) + y[1:]])
    very_annoying_points_g2.append([x, bytes([y[0] | 0xC0]) + y[1:]])
    very_annoying_points_g2.append([x, y[:32] + bytes([y[32] | 0x80]) + y[33:]])
    very_annoying_points_g2.append([x, y[:32] + bytes([y[32] | 0x40]) + y[33:]])
    very_annoying_points_g2.append([x, y[:32] + bytes([y[32] | 0xC0]) + y[33:]])


def exact_cu_cost(data_vec):
    return CU_BASE + CU_PER_ELEM * len(data_vec) * len(data_vec)


def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]


test_vectors_add = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1547
    # invalid op
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": 1,  # sub not implemented
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": 4,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1551
    # cost
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1553-L1565
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START + 1,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START + 100,
        "cu_avail": ADD_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1580-L1589
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L164
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d700",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ + 1,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L173
    # this can never happen
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L175
    {
        "heap_prefix": base64.b16decode(
            "ffb18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L179
    # this can never happen
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L181
    {
        "heap_prefix": base64.b16decode(
            "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17ff",
            True,
        ),
        "op": ADD_OP,
        "input_addr": HEAP_START,
        "input_size": ADD_SZ,
        "result_addr": HEAP_START,
        "cu_avail": ADD_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L191
    # this can never happen
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L195
    # this can never happen
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1594
    # this can never happen
]
# from src/ballet/bn254/test_bn254.c
add_inputs = [
    "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f3726607c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7",
    "2243525c5efd4b9c3d3c45ac0ca3fe4dd85e830a4ce6b65fa1eeaee202839703301d1d33be6da8e509df21cc35964723180eed7532537db9ae5e7d48f195c91518b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f37266",
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "",
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",
    "17c139df0efee0f766bc0204762b774362e4ded88953a39ce849a8a7fa163fa901e0559bacb160664764a357af8a9fe70baa9258e0b959273ffc5718c6d4cc7c039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98",
]
for test in add_inputs:
    input = base64.b16decode(test, True)
    test_vectors_add.append(
        {
            "heap_prefix": bytes([0] * 64) + input,
            "op": ADD_OP,
            "input_addr": HEAP_START + 64,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": ADD_CU,
        }
    )


test_vectors_mul = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1551
    # cost
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c2",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ,
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1553-L1565
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c2",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START + 1,
        "input_size": MUL_SZ,
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c2",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ,
        "result_addr": HEAP_START + 100,
        "cu_avail": MUL_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1580-L1589
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c2",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ,
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L202
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c200",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ + 1,  # implementation bug
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c200",
            True,
        )
        + bytes([0] * 32),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ + 33,
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L211
    # this can never happen
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L213
    {
        "heap_prefix": base64.b16decode(
            "ffd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c2",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ,
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L217
    {
        "heap_prefix": base64.b16decode(
            "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb204ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            True,
        ),
        "op": MUL_OP,
        "input_addr": HEAP_START,
        "input_size": MUL_SZ,
        "result_addr": HEAP_START,
        "cu_avail": MUL_CU,
    },
]
# from src/ballet/bn254/test_bn254.c
mul_inputs = [
    "2bd3e6d0f3b142924f5ca7b49ce5b9d54c4703d7ae5648e61d02268b1a0a9fb721611ce0a6af85915e2f1d70300909ce2e49dfad4a4619c8390cae66cefdb20400000000000000000000000000000000000000000000000011138ce750fa15c2",
    "070a8d6a982153cae4be29d434e8faef8a47b274a053f5a4ee2a6c9c13c31e5c031b8ce914eba3a9ffb989f9cdd5b0f01943074bf4f0f315690ec3cec6981afc30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd46",
    "025a6f4181d2b4ea8b724290ffb40156eb0adb514c688556eb79cdea0752c2bb2eff3f31dea215f1eb86023a133a996eb6300b44da664d64251d05381bb8a02e183227397098d014dc2822db40c0ac2ecbc0b548b438e5469e10460b6c3e7ea3",
    "1a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "1a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f630644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000",
    "1a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000100000000000000000000000000000000",
    "1a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000009",
    "1a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe31a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f60000000000000000000000000000000000000000000000000000000000000001",
    "17c139df0efee0f766bc0204762b774362e4ded88953a39ce849a8a7fa163fa901e0559bacb160664764a357af8a9fe70baa9258e0b959273ffc5718c6d4cc7cffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "17c139df0efee0f766bc0204762b774362e4ded88953a39ce849a8a7fa163fa901e0559bacb160664764a357af8a9fe70baa9258e0b959273ffc5718c6d4cc7c30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000",
    "17c139df0efee0f766bc0204762b774362e4ded88953a39ce849a8a7fa163fa901e0559bacb160664764a357af8a9fe70baa9258e0b959273ffc5718c6d4cc7c0000000000000000000000000000000100000000000000000000000000000000",
    "17c139df0efee0f766bc0204762b774362e4ded88953a39ce849a8a7fa163fa901e0559bacb160664764a357af8a9fe70baa9258e0b959273ffc5718c6d4cc7c0000000000000000000000000000000000000000000000000000000000000009",
    "17c139df0efee0f766bc0204762b774362e4ded88953a39ce849a8a7fa163fa901e0559bacb160664764a357af8a9fe70baa9258e0b959273ffc5718c6d4cc7c0000000000000000000000000000000000000000000000000000000000000001",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d9830644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d980000000000000000000000000000000100000000000000000000000000000000",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d980000000000000000000000000000000000000000000000000000000000000009",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d980000000000000000000000000000000000000000000000000000000000000001",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d98",
    "039730ea8dff1254c0fee9c0ea777d29a9c710b7e616683f194f18c43b43b869073a5ffcc6fc7a28c30723d6e58ce577356982d65b833a5a5c15bf9024b43d9800000000000000000000000000000001",
]
for test in mul_inputs:
    input = base64.b16decode(test, True)
    test_vectors_mul.append(
        {
            "heap_prefix": bytes([0] * 64) + input,
            "op": MUL_OP,
            "input_addr": HEAP_START + 64,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": MUL_CU,
        }
    )
for point in very_annoying_points:
    for scalar in annoying_scalars:
        input = point[0] + point[1] + scalar
        test_vectors_mul.append(
            {
                "heap_prefix": bytes([0] * 64) + input,
                "op": MUL_OP,
                "input_addr": HEAP_START + 64,
                "input_size": len(input),
                "result_addr": HEAP_START,
                "cu_avail": MUL_CU,
            }
        )

test_vectors_pairing = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1551
    # cost
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": PAIRING_SZ,
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1553-L1565
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START + 1,
        "input_size": PAIRING_SZ,
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": PAIRING_SZ,
        "result_addr": HEAP_START + 360,
        "cu_avail": PAIRING_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1580-L1589
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": PAIRING_SZ,
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
    {
        "heap_prefix": [0] * 32,
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": 0,
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L244
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": PAIRING_SZ - 1,  # implementation bug
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": 191,  # implementation bug
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L261
    {
        "heap_prefix": base64.b16decode(
            "ff76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": PAIRING_SZ,
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/program/src/alt_bn128/mod.rs#L273
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7dff",
            True,
        ),
        "op": PAIRING_OP,
        "input_addr": HEAP_START,
        "input_size": PAIRING_SZ,
        "result_addr": HEAP_START,
        "cu_avail": PAIRING_CU,
    },
]
# from src/ballet/bn254/test_bn254.c
pairing_inputs = [
    "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "2eca0c7238bf16e83e7a1e6c5d49540685ff51380f309842a98561558019fc0203d3260361bb8451de5ff5ecd17f010ff22f5c31cdf184e9020b06fa5997db841213d2149b006137fcfb23036606f848d638d576a120ca981b5b1a5f9300b3ee2276cf730cf493cd95d64677bbb75fc42db72513a4c1e387b476d056f80aa75f21ee6226d31426322afcda621464d0611d226783262e21bb3bc86b537e986237096df1f82dff337dd5972e32a8ad43e28a78a96a823ef1cd4debe12b6552ea5f06967a1237ebfeca9aaae0d6d0bab8e28c198c5a339ef8a2407e31cdac516db922160fa257a5fd5b280642ff47b65eca77e626cb685c84fa6d3b6882a283ddd1198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd216da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba2e89718ad33c8bed92e210e81d1853435399a271913a6520736a4729cf0d51eb01a9e2ffa2e92599b68e44de5bcf354fa2642bd4f26b259daa6f7ce3ed57aeb314a9a87b789a58af499b314e13c3d65bede56c07ea2d418d6874857b70763713178fb49a2d6cd347dc58973ff49613a20757d0fcc22079f9abd10c3baee245901b9e027bd5cfc2cb5db82d4dc9677ac795ec500ecd47deee3b5da006d6d049b811d7511c78158de484232fc68daf8a45cf217d1c2fae693ff5871e8752d73b21198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "2f2ea0b3da1e8ef11914acf8b2e1b32d99df51f5f4f206fc6b947eae860eddb6068134ddb33dc888ef446b648d72338684d678d2eb2371c61a50734d78da4b7225f83c8b6ab9de74e7da488ef02645c5a16a6652c3c71a15dc37fe3a5dcb7cb122acdedd6308e3bb230d226d16a105295f523a8a02bfc5e8bd2da135ac4c245d065bbad92e7c4e31bf3757f1fe7362a63fbfee50e7dc68da116e67d600d9bf6806d302580dc0661002994e7cd3a7f224e7ddc27802777486bf80f40e4ca3cfdb186bac5188a98c45e6016873d107f5cd131f3a3e339d0375e58bd6219347b008122ae2b09e539e152ec5364e7e2204b03d11d3caa038bfc7cd499f8176aacbee1f39e4e4afc4bc74790a4a028aff2c3d2538731fb755edefd8cb48d6ea589b5e283f150794b6736f670d6a1033f9b46c6f5204f50813eb85c8dc4b59db1c5d39140d97ee4d2b36d99bc49974d18ecca3e7ad51011956051b464d9e27d46cc25e0764bb98575bd466d32db7b15f582b2d5c452b36aa394b789366e5e3ca5aabd415794ab061441e51d01e94640b7e3084a07e02c78cf3103c542bc5b298669f211b88da1679b0b64a63b7e0e7bfe52aae524f73a55be7fe70c7e9bfc94b4cf0da1213d2149b006137fcfb23036606f848d638d576a120ca981b5b1a5f9300b3ee2276cf730cf493cd95d64677bbb75fc42db72513a4c1e387b476d056f80aa75f21ee6226d31426322afcda621464d0611d226783262e21bb3bc86b537e986237096df1f82dff337dd5972e32a8ad43e28a78a96a823ef1cd4debe12b6552ea5f",
    "20a754d2071d4d53903e3b31a7e98ad6882d58aec240ef981fdf0a9d22c5926a29c853fcea789887315916bbeb89ca37edb355b4f980c9a12a94f30deeed30211213d2149b006137fcfb23036606f848d638d576a120ca981b5b1a5f9300b3ee2276cf730cf493cd95d64677bbb75fc42db72513a4c1e387b476d056f80aa75f21ee6226d31426322afcda621464d0611d226783262e21bb3bc86b537e986237096df1f82dff337dd5972e32a8ad43e28a78a96a823ef1cd4debe12b6552ea5f1abb4a25eb9379ae96c84fff9f0540abcfc0a0d11aeda02d4f37e4baf74cb0c11073b3ff2cdbb38755f8691ea59e9606696b3ff278acfc098fa8226470d03869217cee0a9ad79a4493b5253e2e4e3a39fc2df38419f230d341f60cb064a0ac290a3d76f140db8418ba512272381446eb73958670f00cf46f1d9e64cba057b53c26f64a8ec70387a13e41430ed3ee4a7db2059cc5fc13c067194bcc0cb49a98552fd72bd9edb657346127da132e5b82ab908f5816c826acb499e22f2412d1a2d70f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2198a1f162a73261f112401aa2db79c7dab1533c9935c77290a6ce3b191f2318d198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c103188585e2364128fe25c70558f1560f4f9350baf3959e603cc91486e110936198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "105456a333e6d636854f987ea7bb713dfd0ae8371a72aea313ae0c32c0bf10160cf031d41b41557f3e7e3ba0c51bebe5da8e6ecd855ec50fc87efcdeac168bcc0476be093a6d2b4bbf907172049874af11e1b6267606e00804d3ff0037ec57fd3010c68cb50161b7d1d96bb71edfec9880171954e56871abf3d93cc94d745fa114c059d74e5b6c4ec14ae5864ebe23a71781d86c29fb8fb6cce94f70d3de7a2101b33461f39d9e887dbb100f170a2345dde3c07e256d1dfa2b657ba5cd030427000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000021a2c3013d2ea92e13c800cde68ef56a294b883f6ac35d25f587c09b1b3c635f7290158a80cd3d66530f74dc94c94adb88f5cdb481acca997b6e60071f08a115f2f997f3dbd66a7afe07fe7862ce239edba9e05c5afff7f8a1259c9733b2dfbb929d1691530ca701b4a106054688728c9972c8512e9789e9567aae23e302ccd75",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed275dc4a288d1afb3cbb1ac09187524c7db36395df7be3b99e673b13a075a65ec1d9befcd05a5323e6da4d435f3b617cdb3af83285c2df711ef39c01571827f9d",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002203e205db4f19b37b60121b83a7333706db86431c6d835849957ed8c3928ad7927dc7234fd11d3e8c36c59277c3e6f149d5cd3cfa9a62aee49f8130962b4b3b9195e8aa5b7827463722b8c153931579d3505566b4edf48d498e185f0509de15204bb53b8977e5f92a0bc372742c4830944a59b4fe6b1c0466e2a6dad122b5d2e030644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd31a76dae6d3272396d0cbe61fced2bc532edac647851e3ac53ce1cc9c7e645a83198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
    "105456a333e6d636854f987ea7bb713dfd0ae8371a72aea313ae0c32c0bf10160cf031d41b41557f3e7e3ba0c51bebe5da8e6ecd855ec50fc87efcdeac168bcc0476be093a6d2b4bbf907172049874af11e1b6267606e00804d3ff0037ec57fd3010c68cb50161b7d1d96bb71edfec9880171954e56871abf3d93cc94d745fa114c059d74e5b6c4ec14ae5864ebe23a71781d86c29fb8fb6cce94f70d3de7a2101b33461f39d9e887dbb100f170a2345dde3c07e256d1dfa2b657ba5cd030427000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000021a2c3013d2ea92e13c800cde68ef56a294b883f6ac35d25f587c09b1b3c635f7290158a80cd3d66530f74dc94c94adb88f5cdb481acca997b6e60071f08a115f2f997f3dbd66a7afe07fe7862ce239edba9e05c5afff7f8a1259c9733b2dfbb929d1691530ca701b4a106054688728c9972c8512e9789e9567aae23e302ccd75",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa000000000000000000000000000000000000000000000000000000000000000130644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd45198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c21800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
]
for test in pairing_inputs:
    input = base64.b16decode(test, True)
    test_vectors_pairing.append(
        {
            "heap_prefix": bytes([0] * 32) + input,
            "op": PAIRING_OP,
            "input_addr": HEAP_START + 32,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": PAIRING_CU + 12121 * 20,  # enough CUs for all tests
        }
    )
# pairing checks G2 subgroup membership, so we should run through the G2 (very) annoying points
for g2 in very_annoying_points_g2:
    input = annoying_points[1][0] + annoying_points[1][1] + g2[0] + g2[1]
    test_vectors_pairing.append(
        {
            "heap_prefix": bytes([0] * 32) + input,
            "op": PAIRING_OP,
            "input_addr": HEAP_START + 32,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": PAIRING_CU + 12121 * 20,  # enough CUs for all tests
        }
    )
# pairing checks G2 subgroup membership, so we should run through the G2 (very) annoying points
for g1 in very_annoying_points:
    input = g1[0] + g1[1] + annoying_points_g2[1][0] + annoying_points_g2[1][1]
    test_vectors_pairing.append(
        {
            "heap_prefix": bytes([0] * 32) + input,
            "op": PAIRING_OP,
            "input_addr": HEAP_START + 32,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": PAIRING_CU + 12121 * 20,  # enough CUs for all tests
        }
    )


test_vectors_compress_g1 = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1890
    # invalid op
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41",
            True,
        ),
        "op": 4,
        "input_addr": HEAP_START,
        "input_size": COMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G1_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1813
    # cost
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41",
            True,
        ),
        "op": COMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G1_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1815-L1827
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41",
            True,
        ),
        "op": COMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G1_SZ - 1,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G1_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41",
            True,
        ),
        "op": COMP_G1_OP,
        "input_addr": HEAP_START + 1,
        "input_size": COMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G1_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41",
            True,
        ),
        "op": COMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G1_SZ,
        "result_addr": HEAP_START + 33,
        "cu_avail": COMP_G1_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1834-L1847
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f593034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41",
            True,
        ),
        "op": COMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G1_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59002f7149c03b2c47b35163356519d1179affcf3b9487f7f857c3f11331120e06",
            True,
        ),
        "op": COMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G1_CU,
    },
    # firedancer
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L17
    # - https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254_g1.c#L263
    # - https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254_g1.c#L267
    # - https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254_g1.c#L272
    # - https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254_g1.c#L274
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L27
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L34
    # these are done via the very_annoying_points
]
for point in very_annoying_points:
    input = point[0] + point[1]
    test_vectors_compress_g1.append(
        {
            "heap_prefix": bytes([0] * 32) + input,
            "op": COMP_G1_OP,
            "input_addr": HEAP_START + 32,
            "input_size": COMP_G1_SZ,
            "result_addr": HEAP_START,
            "cu_avail": COMP_G1_CU,
        }
    )

test_vectors_decompress_g1 = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1813
    # cost
    {
        "heap_prefix": base64.b16decode(
            "9c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59", True
        )
        + bytes([0] * 32),
        "op": DECOMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G1_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1815-L1827
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "9c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59", True
        )
        + bytes([0] * 32),
        "op": DECOMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G1_SZ - 1,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G1_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "9c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59", True
        )
        + bytes([0] * 32),
        "op": DECOMP_G1_OP,
        "input_addr": HEAP_START + 33,
        "input_size": DECOMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G1_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "9c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59", True
        )
        + bytes([0] * 32),
        "op": DECOMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G1_SZ,
        "result_addr": HEAP_START + 1,
        "cu_avail": DECOMP_G1_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1834-L1847
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "9c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59", True
        )
        + bytes([0] * 32),
        "op": DECOMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G1_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59", True
        )
        + bytes([0] * 32),
        "op": DECOMP_G1_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G1_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G1_CU,
    },
    # firedancer
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L43
    # - https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254_field.c#78
    # - https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254_field.c#90
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L52
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L62
    # - ...
    # https://github.com/firedancer-io/firedancer/blob/a8c2e27b/src/ballet/bn254/fd_bn254.c#L67
    # tested above (success cases)
]
for point in very_annoying_points:
    input = point[0]
    test_vectors_decompress_g1.append(
        {
            "heap_prefix": bytes([0] * 64) + input,
            "op": DECOMP_G1_OP,
            "input_addr": HEAP_START + 64,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": DECOMP_G1_CU,
        }
    )

test_vectors_compress_g2 = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1813
    # cost
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550",
            True,
        ),
        "op": COMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G2_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1815-L1827
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550",
            True,
        ),
        "op": COMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G2_SZ - 1,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G2_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550",
            True,
        ),
        "op": COMP_G2_OP,
        "input_addr": HEAP_START + 1,
        "input_size": COMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G2_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550",
            True,
        ),
        "op": COMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G2_SZ,
        "result_addr": HEAP_START + 65,
        "cu_avail": COMP_G2_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1834-L1847
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416782bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550",
            True,
        ),
        "op": COMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G2_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a4167804ac1c27ea61d6f480ad989c3d245b50f4da4fc3edadaadf7c8d4fec86bec8fa1e5a2425ee25843033f124ef834777def4b484725bd61a4525c0a631f9f587f7",
            True,
        ),
        "op": COMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": COMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": COMP_G2_CU,
    },
]
for point in very_annoying_points_g2:
    input = point[0] + point[1]
    test_vectors_compress_g2.append(
        {
            "heap_prefix": bytes([0] * 64) + input,
            "op": COMP_G2_OP,
            "input_addr": HEAP_START + 64,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": COMP_G2_CU,
        }
    )

test_vectors_decompress_g2 = [
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1813
    # cost
    {
        "heap_prefix": base64.b16decode(
            "a09dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678",
            True,
        )
        + bytes([0] * 64),
        "op": DECOMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G2_CU - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1815-L1827
    # i/o
    {
        "heap_prefix": base64.b16decode(
            "a09dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678",
            True,
        )
        + bytes([0] * 64),
        "op": DECOMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G2_SZ - 1,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G2_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "a09dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678",
            True,
        )
        + bytes([0] * 64),
        "op": DECOMP_G2_OP,
        "input_addr": HEAP_START + 65,
        "input_size": DECOMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G2_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "a09dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678",
            True,
        )
        + bytes([0] * 64),
        "op": DECOMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G2_SZ,
        "result_addr": HEAP_START + 1,
        "cu_avail": DECOMP_G2_CU,
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1834-L1847
    # actual op - all these tests either return Ok(0) or Ok(1)
    {
        "heap_prefix": base64.b16decode(
            "a09dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678",
            True,
        )
        + bytes([0] * 64),
        "op": DECOMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G2_CU,
    },
    {
        "heap_prefix": base64.b16decode(
            "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf704bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678",
            True,
        )
        + bytes([0] * 64),
        "op": DECOMP_G2_OP,
        "input_addr": HEAP_START,
        "input_size": DECOMP_G2_SZ,
        "result_addr": HEAP_START,
        "cu_avail": DECOMP_G2_CU,
    },
]
for point in very_annoying_points_g2:
    input = point[0]
    test_vectors_decompress_g2.append(
        {
            "heap_prefix": bytes([0] * 128) + input,
            "op": DECOMP_G2_OP,
            "input_addr": HEAP_START + 128,
            "input_size": len(input),
            "result_addr": HEAP_START,
            "cu_avail": DECOMP_G2_CU,
        }
    )

test_vectors_group = (
    _into_key_data("a", test_vectors_add)
    + _into_key_data("m", test_vectors_mul)
    + _into_key_data("p", test_vectors_pairing)
)

test_vectors_compression = (
    _into_key_data("c1", test_vectors_compress_g1)
    + _into_key_data("d1", test_vectors_decompress_g1)
    + _into_key_data("c2", test_vectors_compress_g2)
    + _into_key_data("d2", test_vectors_decompress_g2)
)

features = [
    0xAAEF1EDEB6C5BF85,  # enable_alt_bn128_syscall
    0x9BB55B5DF1C396C5,  # enable_alt_bn128_compression_syscall
    0x8BA9E9038D9FDCFF,  # simplify_alt_bn128_syscall_error_codes
]

if __name__ == "__main__":
    print("Generating syscall alt_bn128 tests...")

    for key, test in test_vectors_group:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = b"sol_alt_bn128_group_op"
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("op", 0)
        syscall_ctx.vm_ctx.r2 = test.get("input_addr", 0)
        syscall_ctx.vm_ctx.r3 = test.get("input_size", 0)
        syscall_ctx.vm_ctx.r4 = test.get("result_addr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        syscall_ctx.instr_ctx.epoch_context.features.features.extend(features)

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")
    print("Generating syscall alt_bn128_compression tests...")

    for key, test in test_vectors_compression:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = b"sol_alt_bn128_compression"
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("op", 0)
        syscall_ctx.vm_ctx.r2 = test.get("input_addr", 0)
        syscall_ctx.vm_ctx.r3 = test.get("input_size", 0)
        syscall_ctx.vm_ctx.r4 = test.get("result_addr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        syscall_ctx.instr_ctx.epoch_context.features.features.extend(features)

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")
