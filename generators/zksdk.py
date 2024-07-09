import base64
import fd58
import hashlib
import test_suite.invoke_pb2 as invoke_pb
import test_suite.context_pb2 as context_pb
from enum import Enum

OUTPUT_DIR = "./test-vectors/instr/tests/zksdk"

program_id = "ZkE1Gama1Proof11111111111111111111111111111"
accounts = []

class ix(Enum):
    CloseContextState = 0,
    VerifyZeroCiphertext = 1,
    VerifyCiphertextCiphertextEquality = 2,
    VerifyCiphertextCommitmentEquality = 3,
    VerifyPubkeyValidity = 4,
    VerifyPercentageWithCap = 5,
    VerifyBatchedRangeProofU64 = 6,
    VerifyBatchedRangeProofU128 = 7,
    VerifyBatchedRangeProofU256 = 8,
    VerifyGroupedCiphertext2HandlesValidity = 9,
    VerifyBatchedGroupedCiphertext2HandlesValidity = 10,
    VerifyGroupedCiphertext3HandlesValidity = 11,
    VerifyBatchedGroupedCiphertext3HandlesValidity = 12,

CTX_STATE_LEN = [
    0,
    3 * 32,      # VerifyZeroCiphertext
    6 * 32,      # VerifyCiphertextCiphertextEquality
    4 * 32,      # VerifyCiphertextCommitmentEquality
    1 * 32,      # VerifyPubkeyValidity
    3 * 32 + 8,  # VerifyPercentageWithCap
    8 * 32 + 8,  # VerifyBatchedRangeProofU64
    8 * 32 + 8,  # VerifyBatchedRangeProofU128
    8 * 32 + 8,  # VerifyBatchedRangeProofU256
    5 * 32,      # VerifyGroupedCiphertext2HandlesValidity
    8 * 32,      # VerifyBatchedGroupedCiphertext2HandlesValidity
    7 * 32,      # VerifyGroupedCiphertext3HandlesValidity
    11 * 32,     # VerifyBatchedGroupedCiphertext3HandlesValidity
]

test_vectors_agave = [
    # {
    #     "ix": ix.CloseContextState,
    #     "cu": 3300,
    #     "data": [
    #     ]
    # },
    {
        # general case: encryption of 0
        # https://github.com/anza-xyz/agave/blob/v2.0.1/zk-sdk/src/zk_elgamal_proof_program/proof_data/zero_ciphertext.rs#L113-L117
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ]
    },
    {
        # general case: encryption of > 0
        # https://github.com/anza-xyz/agave/blob/v2.0.1/zk-sdk/src/zk_elgamal_proof_program/proof_data/zero_ciphertext.rs#L119-L123
        # returns error
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "5ebdea7de36c7b07cdfd618167c91252834ef484cde91d1bf6d57a46b994973c",
            "8243dac0622ff89fbe3adaf65517510002bdd89262724749383fb5631e394e51",
            "a682b5ec9826c088eec4e73eb32e44dd6aafe82e4dc81a8232228674c44a0f0f", # proof
            "12e1f9a9b28f8369087d2634a6ace3bc5c022f1c0c8b75e7e6f9e74d2134177c",
            "e3f971442fb3980feb89723edb8371cf55d313591b26c27dbfc7922e82811200",
        ]
    },
    {
        # amount = 0
        "ix": ix.VerifyCiphertextCiphertextEquality,
        "cu": 8_000,
        "data": [
            "6203276d8810327eeccbe1fcde04630ff250e94d49a437e51a6f2d4d9590bd21", # context
            "745458e97ec64727f8a67a7436b7557c0b8f891e44c9c136f6d58014fae34b5a",
            "e646b35db798d5405795bd1bb214059a7fc216237124732f1b823e30f8a78a18",
            "448ff1b685a53c6762d5e99dccd7eca83ffadc42f7e91bd58e4eed3d60bef743",
            "b8c6766f725b6788522d2bf259acc441286e38744a0511324d4ca4f5e1b17425",
            "6edc925435cd6472ba90e2c2e3a5c2ffd69d2902beb8ede2b1a6cc1e27f2e609",
            "7e6104e02e4351bb8de580abe38bad577e9eeb71b3542d4ea55ef10768487c45", # proof
            "20b2366fc926ff2e8ce9a9e1a89e3f1ff0ccae530284dd71ae3a44988924014b",
            "58f080067a2d07c1e54ae6fbc4371cf1cea6bf4bc3297f29c244e3f85ea7785f",
            "02f827c666a2de308bfa6329a69f75eb90badf1ebf8db02567fd93bcfc98ba68",
            "408a076b4ee323504aa7d3486c815b0ff5d5d1706e7a5d95580dbe298247880e",
            "1e7705737c330ecc93565ce24156259c680e1ff9035038498ae87d4b1977cd05",
            "b2db2991ecb27bb6178d878dec5a791634faca7a9d6e829e2777335f32c01b07",
        ]
    },
    {
        # amount = 55
        "ix": ix.VerifyCiphertextCiphertextEquality,
        "cu": 8_000,
        "data": [
            "6203276d8810327eeccbe1fcde04630ff250e94d49a437e51a6f2d4d9590bd21", # context
            "745458e97ec64727f8a67a7436b7557c0b8f891e44c9c136f6d58014fae34b5a",
            "8865734bf7df68f0b38fb912e01d8649aa8a36b9b76060c974caac3ad3cb3c01",
            "feac55eb5566f7b291bd04fbcf734ea39f33f70eb8bb9c838a6f94b4a4055018",
            "2c7ebfb0fc1cd268575d73e5580cb1b567e00a27f46c0efb0d3324335d1bee78",
            "cc3cde7f28a2fb54fc1f09ebd12792de31fd56bc3532b3f3d5b11c110533e95e",
            "d2507d05a62c466d34f86c93a079697c3590bb9003e7ccbe2148f1fd35379b1b", # proof
            "5c4aa6ff20096d0f3fc9124d1ba6ad00e20d80fe87781ccfea6581aa7f822055",
            "2e2e4479069f8701a546c82b9e3f12f11b43f913f6e6225f87675fabdbc3a528",
            "769a3f877a9b69e3d380d130b11378a0d89634baaece3957136a79717ef0fc79",
            "3a16a7543fcbb935bf5ffa0338b3b443ec520712286abaaa8a79ae09340c2c05",
            "d55a9406112b1c42ff0f9be91306825e319e3e23cba8d526217b0c64bafee80b",
            "37e9774e91868cdf3a80d4176b2735b5238509782beb46ac9639949e5d49df0b",
        ]
    },
    {
        # amount = u64::MAX
        "ix": ix.VerifyCiphertextCiphertextEquality,
        "cu": 8_000,
        "data": [
            "6203276d8810327eeccbe1fcde04630ff250e94d49a437e51a6f2d4d9590bd21", # context
            "745458e97ec64727f8a67a7436b7557c0b8f891e44c9c136f6d58014fae34b5a",
            "acdb17462a7ee7e143ef0c4ab0dd9b53fa50ea4baedce266c940b13e09080903",
            "bc671397d5e16e6ad4e752e3e0025dd9cef5012d68b6b6a91b1d151322259410",
            "ae79869896b1c732dff245c6a970a81922f5b3b0c877da30b2bf2e39393d087e",
            "06c0b007cb5bc06c9d2bb78eda95d63ece9371d5aec89c1c8518b62ec2eff836",
            "dc0238da29425bb40588e3f3593c246e359e10d11f23cd5393db6b4268b4e954", # proof
            "0c3cecc3425401561f828dd95bd8b2e05c53145fa602d4445330b3bf442c6541",
            "b61d64ca455b8d7eedeaac7f6e71603a817bd9ed29b4e6ad69176cfa26886174",
            "5cb1bb0d52afe8ab1ea0854c8f8da83f53f33a245e5c6f2765e456e232fc0178",
            "487717f393bb1a75f4b82c79e4876299c58109e2cf7202d172f565d461810402",
            "68afd7dbe77d8ef21be7f9454df8cd31164b2a52b72c3f1009128ab7f6776c07",
            "b18a7d0ce6e3b781b31620fe1e9e76eb6ca84def8b05235b451f6d0aaaaa5501",
        ]
    },
    {
        "ix": ix.VerifyCiphertextCommitmentEquality,
        "cu": 6_400,
        "data": [
            "da90fe53085362f1a2c9e744c9e63ef22e25e92244da958b26353be64927456f", # context
            "a87b22ff89e686cb2e77d7c41a511a32b4f6005acf9729b509e6ed277d65666b",
            "9e02767403d9f601f97fdc6b994781c95b498ffc0da248ebd361da78e324a455",
            "226ca48cb9f90f5a314d0d5498dfcd61087bb788f356eea98aa63bc00ba30764",
            "50e3d9247328ee1316c821904878378950b1f1e4c7c4f084ccf6d7ca96725e59", # proof
            "f857d456e45d927d5fa61bb22ee9617ef1fbeb3bb83d4b80802e22d5e9588716",
            "b6047476954068f3dc0f0cd8636a149f4722f71ea4f2d68287f352539c43b901",
            "6fafc54f9817635113f6615a198c81650ddb8f4284853d83feee69469be0790f",
            "e03048146cf8982c356dbdfa3d2431e579afd3a8e2836a8c640cb65b7bf54803",
            "3fa0f9bf71497419e542b1e454ae14700622b1beee05a86d06ec5dd4e60ed90a",
        ]
    },
    {
        "ix": ix.VerifyPubkeyValidity,
        "cu": 2_600,
        "data": [
            "fa89ae0c8312aba69e727036a794b5add351b020e43c65ea94cdda8d8f8c2037", # context
            "80395515497f92fa09ebdb5f14b7f6b32ab8abc3bf7349394b538fb3959c8c4b", # proof
            "0e5cdb1f8f9aeb2fd374b89beafaf2f47a0b83558a7ef94629b07101f50b0007",
        ]
    },
    {
        "ix": ix.VerifyPercentageWithCap,
        "cu": 6_500,
        "data": [
            "c033774789b2fc16b632192638070e15b6b59852488d9f2a92c758e90b30a45f", # context
            "f8691d53d5d8e1444e9a3eefd1f6e0fb6c6ed08f31a0b86e265454e097e1f219",
            "7649f6d240769e77c186a610ea5a9c9942d1e6f98031ac38693f1f63d9023107",
            "0300000000000000",                                                 # proof
            "747e6ea4ae760a10728adf0916526562f3ce32e905c4fc724a6ae4be7cca1e1b",
            "8bb081de00196a204258893e3b1b6af6c55b2e90f91a2d91fbc01c0fe8f20a08",
            "d3b14114d91fee677cbd6471a27a2c3df2cfe680cd9f169cc19a3837668e5209",
            "34e57f984a4928baae7a39c0788104630dc80382414ed991cc669ac6ca762749",
            "3a9253d7f1a84d6808b0a0fb6ebf8eb0fc80cd3d9909715d5594e1280916f811",
            "d1034395df8f507896d247f1003333b0bc1d31514c4d56ec774713c9cd70e200",
            "b47e3d15dcadd2dabd8bf392fa564b0a0b170cf4341e6f4bbeb6656600038d03",
            "48bc7b57bf09b1c432d9f66c925cb4fad1c3d5ae37a90235a56ef21d7f0c6000",
        ]
    },
    {
        "ix": ix.VerifyPercentageWithCap,
        "cu": 6_500,
        "data": [
            "1223b394709edb8003d23630597f5a58eac0894d1bcef409cbb597e8b5269f5f", # context
            "242777cd165c5b2931163d1712bf0aaba3ee58176b01d29afe5ab424d5b7b705",
            "dc4ccbd5728ceb309b1d49d18f3bee3f62b4e290a514a8e28d0600245b99722c",
            "0300000000000000",                                                 # proof
            "5678659d22f233faf43255f4e2965f01eb9bcb6081ef5638e8547b40e048d452",
            "8525ea544486c7d5c0c49367fc195023e734a81f97eb27f5ac7846dab4a34407",
            "b94684c2752461882c61b7d202d8885aeda0356629265ae7427d69f6fd62fb0f",
            "e2587b37d430ca559fd179174798480bb65ed8bce322e4c678b0b694b41f470d",
            "146bfe3371058201e586ffaf1ea567863d6d5cfd2fd4965b3c12c1087b3d1e70",
            "f262079021451a0970b49646b60462cf4ac4bd6feb709ba6df1d90f84fc74b0a",
            "bfc6497a0661a4379447de1038017a43833d4b77f7aff40d0f6c31eb5a81a605",
            "3d0af260d8a61f67fec606424d6ebdd20b62435e230ed75366d052f475e4130a",
        ]
    },
    {
        "ix": ix.VerifyBatchedRangeProofU64,
        "cu": 111_000,
        "data": [
            "8ce8dcd01b60676db1f43763c06a3fc05db0776728c10f9c7a439da853459068",
            "1c554814d288aa33250aac204f5927f88f651c79dc2a451d1efb9f0fadb4e86c",
            "60546b4274a7c1f134c0738449463eb131c10fedb4a70db622ec4d144b469e23",
            "a0942fd4661e490e93a420f9943cc809985addaeb29aee507e3d4fa940e93229",
            "b0577d102ff4bea9317bbd01cd8cc3041247a314e467a9017aa7a9273e525509",
            "de9710b98d6b67961995007813e3105dffd096acc45cd3c020dc9ace3a3a1c20",
            "5e6de66bf9d7e0d864a165728f74375dd107a40d6d83f4f4797cbf43b53d683b",
            "2e70c1d283a7a79593d6c0b32458f7de09de2ea9612fb842e3c0dc6d62bfa019",
            "0808080808080808",
            "4c02cf1aabf54c348f85c2808686b4cd6fb61371ecdf83324da6b19c526c0f17",
            "fc4f994600e9d996302b3c115c4e21d49108fd08bdde5254aec8527c0aeae82c",
            "b626481c8fa1fb924ec053fa1f7f75b4f1e1bfae3cf3ad0cd93a5c5db881657a",
            "fc4c6dd76fd83d34b9fe4f67665ab8d33cdc685fc713d89e6a5efacbfd0b6759",
            "5c4ae6427b13755328c67c89a07835c4a4d44b8cf6231177ffcf0fa464946e08",
            "2f2253f8920cad95c5af4b4413727f63d5faac8c1248bc5bafd6d3593dead201",
            "1fd7f812740bd5d20a960c5b40e840b72424524a91eb5cc86ae74c1562b46a03",
            "c25b0cb644a2b6a7e6385d0549ed02769f100b268dd2adc93e3b5043a06dca0c",
            "b4c71131e049d66a8a5fce0841dfa1e3833fef3fb20cade76b7f7e1bf0af456f",
            "5224ac52c16cb24f50a42bc5052c959638a4a0368f1ac2c41c3cdfba9f855a58",
            "b60eec273cabef062a56989e3ade708fca4c44cdc005100c6f112c1d1a51e810",
            "c204eb6ad44db4a539b0e5de6339de5cf3f2ed2041b627fec0569b0c46c66072",
            "9c65a220d867a81fd8163313ea97b002c9e19b33ecc137a1e346f747b7ca2578",
            "ec3469d5f6d239e1b9c6b86f01f17b57b2ea7d3fd5140456688ac0dfd70d2e53",
            "4e0146014f2b35e4f047ffffb8e9956429dc0946208dc747424b32865529613c",
            "b8dd241ef279004485ed5c4f958dea5d14161cdbf3f532888ba5cc16c89ca823",
            "b85eed9ecfeefa49e8026ae75d737223276dc3a38a925767f6c92b7020c21028",
            "7433c06d4e7727034f493eb83900ed2a69bf2f3f91db70192f472fc61dfc6c14",
            "268fb9acbc6a043d84f9c57c6c0d67f0300a48b288a1b95e7d444a3f118a3038",
            "122dd6f4f0880a6fea2f0133478920aa417a46bf9cc022ac8374855eedab5c0f",
            "32725bbda4ec74db73868fbc7b7f432c7456800d5ca582dbda673f402a097a00",
        ]
    },
    {
        # error
        "ix": ix.VerifyBatchedRangeProofU64,
        "cu": 111_000,
        "data": [
            "b879081d5018460d605d5f61c9bddf7d17926a9e474ab50b6528e9de89c9cc3c",
            "be2c79563f2fc74e7d82145fe8bb4da6e6ca54fc3aa5a1174bebb94b608b531e",
            "8a98d2ac5d9b374387b589ac75b8e618246df36b5ef51d3140f47d421151493b",
            "12bc1c7eb2baf8c9c576bc62e79bc12a4904ba1aace93c9fcee1f40f136e1503",
            "5ce0d70fb603ce89d7b4dc65803228b2041474e629c821c083afa77875a7c752",
            "0ab7c1c166ac3dc2a7a84b3d4c89ff51d6bb467ca52afd08e2d2c7824778e100",
            "7ee965bed1dac9ece0ce4c863ec0eacb373c1d4e6f4105e451707289b2cff43f",
            "3a7b142a439845eb51eee764f64a3f8fc44ff1b1de73c7f4d466db63fbb7a56e",
            "0808080808080808",
            "742f4d2eb6a412456d20a015814c0d2a21fa0c3ff14b24c4610d566b9fee692d",
            "f03a6e829a5011cf296a5bc824f0c1318da65b967f920d301babe7b07f09f069",
            "9ca91a2eb8dc10be2a477ea5795f2195f35770ef9962d176eb82ae6167f6bb0e",
            "f8b16067313337e987722066c459bcc5b637e8a7b1901c393d1dbcfd6dae4a37",
            "a688a77b4e2d3742dfe0b74b47dbb00660c1da63be5fda04a531dd03f5685300",
            "2b5455b25e49961ed0028b2d2ba3b2c5e2da96a76f84eb5c22333026453ca50e",
            "dea4179327fba79d6c23a63175acc9da0a3ff0679188c26f804988d84957d807",
            "a8395b1f4677c791200d87bdf801df05cf91c7e8577315e1ad72c90485a98b52",
            "e613a9f9819dd474e16a942a9741972f7d3a79b6ecd1a9d8116e560e15779c78",
            "5e5999f44cfc8f3533af4752783bf94c6889cf95ab750a0eec03676eb499db1b",
            "6aad11c18f3ce7170639a048336cd93ed7b6e2fdce65b97ed3fdd0202efb7305",
            "ac41e5d522e17b4d8a40bd38aae606a0dbfb828a87683ebc91919d0fda353201",
            "622092094333a22b4811d517274bb26be7575b037632c65a76b617a7f120b603",
            "1c6d0c695e79fa26b75dc4bcfa879cb20f5294957a953bc843f26624584cf95e",
            "867bfbf864a96c8159d5b83179c525521ef09a53c2fe1e00e58852ef53817234",
            "0c663682d0a7414c9853928c57a5f09099820876f16ca5e8159fb87534ab2d20",
            "6819ea9db9d3da693d77fd77e6f6a31ddaa443ed1b09a7ae117c2402b22a8558",
            "165ea31d16d3baa52796df3fdb4c9f868ea4fd61c1477e453c18b93563ea1972",
            "ae51e45566a606bf2e430b19cbdd8bb23bf9bc812bc4a53184a395e334397e51",
            "28bb560f21664b30cc9b06a9e38291ad7b3e4b5897acb4eab18946fc93745101",
            "ba1910e4218177c32ea0cbbdef4b13ddb080470bc96d09803efcc1bf87ca260d",
        ]
    },
    {
        "ix": ix.VerifyBatchedRangeProofU128,
        "cu": 200_000,
        "data": [
            "d0f2cfe5fcad79572a6157c1e7514860d68257798c41cdcd14730dc6975d8042",
            "7ea5a1afb7fed3a25b95bf36631f5ad1a837904f136c674a40ee0375f04f266e",
            "42380cb4bb26221c1b5d48ac552bb150d6d0955b15c992f6783222640d01dd51",
            "82b777e41d0e24786880e06b6d77466d16baf92cba47db533316cd819f518277",
            "64ba0c50da2cad1354aaee1b740d50a6d790a39118c7bd348c40dd10d3f7c262",
            "c49303bf623e26e08556209597d54f967cd9c3b30222a5d75954cf3efa7dc022",
            "98c2d4ee820b9d0345a4a450a46d77a69fbbb98ac86d666ab1ab801051493432",
            "3af2caa40032415bd49a5f6c766c2cc6adc5254e9f67723db7c9b70fb080e919",
            "1010101010101010",
            "4a752eb7c8bc1b07bfe63bd72a1a3c7e75b42c7ca7692021f8439caba638b527",
            "88bc210ed9954441e7ddbb6e6fba6c965748991e7f432babcfc78a6d4cd90716",
            "e875094489398d74b168cbeb04f71ba4f42ec25ec4a0a9fc29977d4667bdd118",
            "d2ce9d221e4983371de681c6928f51756df01323581a96393281faaf827bd130",
            "8c90481e860e45091595107015580577a497167dd4703cf0fda14a5b18090b09",
            "b90f99ce2a12f66160f8edaf4dfe3633e53648fdb953e5db4365093396e5b007",
            "3ab7a2b4955a36463c9860c9fbdf3310b9a762bdce80a424b423e0c3297c830a",
            "123662c6ea3391782a7e9d5c3e5967c4f59f50bd35d6630b4e6c1c3bbead3d1e",
            "eccbcbd8e4c547f9113c9831f119b5598dec2337a5550d8c4ee62c01f435ab78",
            "0a4d818c26ef788781432df6d28db7d0c3db4fe8fbc9523c50b93d15f69e431f",
            "3830185b3b7932563f9bcb417821533b18d3e1ebe9f79ba30b4ed9e596e23d46",
            "8a1b613f86e24921009f9ac53ce324ee154ebfe66ab8d15dae675c809b180057",
            "54ba35a5d37b62afdc7ce0e2b932fac093ec6ffae9ad2c3628973d400d3e3231",
            "7a903290e77f460e38b7423925b65d028ffc2d38f806997a123e318f0f24911d",
            "1e482f553da5db2d310421a26b79b53eb4f7e9ee74bccacf31956d6bc7a7114d",
            "183074973781b39d0f0f1e2682e09557961e75d745478612293a525b2a416d2b",
            "1ad54c35b0e6be21c1fa6aa07412dbb1ea3e1d1f6a4ff868583da88e89efcc6f",
            "140651e0915ff7f2dec23f8390e41d1c7307f3cffef22ac05a3acc8457660a1f",
            "345ecc0727f47795c2eeb762172da28099c68fa107dab1a6c78b4c9cc7006577",
            "8a950359b295bf0031f3fa8d15ac2f1878b7003f259ce543b081e8a6b9a3c117",
            "1a6de22b76e8abf1f173941ad96122f71368c2a1f3b601f659898b4e3fd1e724",
            "450e0eac07d13ee2a717b3bf112f3004c651b1d1ceb630239ca972189fa1cb01",
            "376177ca7611edcdfbe559ccf054995bc070d3b65a0372498407729ef6ccc108",
        ]
    },
    {
        # error
        "ix": ix.VerifyBatchedRangeProofU128,
        "cu": 200_000,
        "data": [
            "2ce6eee569d2cdb7ba5efee882345f7360bf68ac3911c176830e284ef9aca76b",
            "a89002ee42802cebbdf52fdc8cba61387a29790a3d6a64553234e1cfadb9a350",
            "100c66b0d478fd7f6afb6cf4f19c8faa9c03be0f0cfedb26a9b93c69d509be61",
            "c08a4139da2e912895337780fe7c53a12be2b42cdfe8475500ea5b3a7bab980f",
            "a0222c77efad367d52b8dc394e166df279e036bd47848afd3274515321e09c02",
            "c43dfbc46e911c7b25d79b514bab8e2ebb0a09e3ee47dd430573a06ededf4642",
            "daf29e81c52cbbbb53f71ab1b83335b52175190dab87feb814426a844069534e",
            "dac873fbd21a4480eb7a5b2c0b05259be7c1603d1a94d716597594b9cc2f8821",
            "1010101010101010",
            "7833683e114cfb3771076f6601b6f57c933a5faefd76e9b2952bfd88b201253c",
            "6e683a3a034a470445b13dfb32968844390e4a12f43d07e2409efa12a95f9579",
            "f4e594383fb7a34370883e0a2efb384fed646da7bbc809c74374eef9101b6e40",
            "a00dec0fd74d8567a5448a290252d717f7c2fa980229ce0974e800cf8ac49b2a",
            "41b17fad37731a68e4c364f3c9b7ab49b4abcc92783df2e5030cde41e235560a",
            "abed39270fa4aa034ed61ead9ec497fb92eeb173512db4bfde669eaa0f49660d",
            "a7426ffa49938dc33ae1615cba55a83d756e11c7fe29abcfbee2c5d49d9f3706",
            "3e31838371aacad4b72ad1ad300150ce15334e2e7b13035fb4c957ed791c0847",
            "1a5fa1f68544a21efa00656fae158069fb036aa7f787f1ed0482defdebccf31e",
            "1216462fdc4ff7590aee9d3a5908f0d09dc65e6e9ee3d7c872c59a8224bc5c00",
            "b8c55777c60f5fee11cafc63b82af97799edf2aa5d6c256b0fd8776650f62112",
            "46c834688709cf0165a0f1870391de208b9f748b2a5c66fd348b601b90406072",
            "e0131cc63b44e22ab862fe5c3f82ad33ff0be9f4f83b29193cdd2bb92b57922f",
            "bee18235f7a5e2e8cb5edb7c4894da28e12389a0503a55a4273be917e028246e",
            "0055d8057c2a24fdb64560fbf55849653ca0d81307e8133f4527ada44650e270",
            "347daa8b18902e7f569ea76ab134042c1914f15ba44dda99c7a5c6bcafdf1559",
            "f6c7298156597a1bfd88591adacf5bff8e32df0e1dd01eb45d2a6c100e2b1667",
            "dcdcbed4d0d0519e061c8e101544c851f0515546bc89dd19f5a79ff26d169970",
            "fa4aaf798d12c964b9a742e1a4231d9dc53db7e3ffeba7ae32f8ad9bce1b916c",
            "7e143c90e0b8af74fdf4aaca883c90fa380a4dc86152b551f5bd95b52f545350",
            "20b1256f8a3c315f4dc5259ffe939342339d9b68e1a7520aa062ea57dd7ca734",
            "847bea4cd799436f329e812f466c38a6156f28f1da43b068aa5ccc33161e380e",
            "67d3f6a21ef6a21b8bb77167ba7fde55741354a320dea17559ce9f6230a01508",
        ]
    },
    {
        "ix": ix.VerifyBatchedRangeProofU256,
        "cu": 368_000,
        "data": [
            "c008da21ceec32bd84da5d9ba6d2d81ac4117c59176b7f99335cf5fa87b3a968",
            "98987fe8ae3a34e5182364191b955f8fefee992042734e6ecc7c359e4e5fa408",
            "40e46f9932abbe3621dedd67f1ec39221e57cbee173c1d685b1e47891e139121",
            "88aa04e5848164e263d73ccbf5cd799b09af69d14993e17482ad3bc722cfad42",
            "e07681d08c40c0455baf9d8c61b3686772ab86939b900b428aee638778b34e57",
            "f0bf28fee99121142eab140d7f8e135cb206f9ed0b71238d6c8b6f3595fc9171",
            "ee621edc316ef64088a6abbfde134de69d6319ba361202890a4a84540372b50b",
            "b42b83b999bacc6d4814302f3c325b820b598b964f7ec47d391b71f1c5fa5604",
            "2020202020202020",
            "f66927fb215ea8809d9e6eebc4ab8727bf75e93236c16896f2700613694a9f4f",
            "989707d546ad988011cfd92e5fa8e048be1c072831fc728e3556e30938eb7349",
            "b6caa7f8786a8ab5be129e8bf7828b51a12d16a57498bff346862f6c52701203",
            "36200aba0505ceffb269dd8ed6ee61adc3eb69d63a33ea5de0c23d222ca7c06a",
            "4e45e957dc3f0cd39f4f8de3ad12568c779cf555da9615e7bf8ba63959536f03",
            "e8f6c683d6ef071c3aa425b233cecfc8bcbf45a51c4928e440410e70b433ed02",
            "0e49467d28ec772dc9d0b168219d5da6af70b6a3b6390e2349bfe9807a6fc406",
            "76177e698d7d95ef453582fbd4c76413c2b20abef233f7b23199132bc21f7e2c",
            "ae935561b86bd681ad0940ccbc4c84aa4762d7136bd4ec57b3866c8cbdef2877",
            "9405e8d99c8f847f4bf4be2d8c36162ec8bbe7516d3c1a289e106f3404745530",
            "0eeb4389ff6f8e37d12a035403d27d8452746cc7c5b74425a3b9be1acc31c16c",
            "40399f4dedd4aff38760b20c50c90a8953645bc7b5c8d4456c38dfe66d504201",
            "023d97856b84d015048d9c7394784d42e9cc9603ee811b22764fe8954d1ce867",
            "8064ee44154411fa5b052e7a55644952589e551d1c625e95de31773dffa88210",
            "c67f801be108bc8690282cf28a4c55b1ab80342ab1cb8cc766e136497e40d847",
            "8e5f7818cca6d282ff69f55487a2fb7fc36a675216ae25a08fbe279461bf5544",
            "960e6abd398a553abc098f567b7ffff2f06daa72ac35d07b657bd80c28e9a528",
            "061f754b945cae6010608cddbb2c1237ce9c11bc3b5348e3e39e9c1787bd8468",
            "8e55e3580caac824c202786f1074ba5c1365c96d26afc9e53690821dd452961e",
            "24b85921849e2922ae27420476a0b1da9cfea1df50a80f17a5493a6bdff9fd52",
            "deaf8069930d3d505371c1c2bc065e7bcae99e8175b15439a1e3a39ad6032914",
            "822b6a8afd5cb10c35b1a87b4446c1e936d2297ee5c4338bb267e75c2eaf5774",
            "b669829fac57cd909057f8e05e43bfe67f00ee354963d336eabd584591adac43",
            "70e2258cdbdb260391aa226872d6d08df229ad3f80714ee8f3201c7045f51106",
            "41994266ce2f2e5eb9fe716ec1725ed66851995379887ecc58e48f74a5a5cc03",
        ]
    },
    {
        # error
        "ix": ix.VerifyBatchedRangeProofU256,
        "cu": 368_000,
        "data": [
            "0aaaefc82a00907a8c14523cc0f296c767149b1a257bb088351bc887a3dca650",
            "96e433b20466bc3fe683516487891f2c5a378c1e1da1ffde32cbb9cf6842a153",
            "206dbeb9f9656b42bd18e6c1bff7f5473f80f01413433c25f21929415bf52c76",
            "be6315fd35e729ba3cab62d08b38a6199c83745131fba41bcf7d492c36283104",
            "fe1c705ac94a86db2dee3e4f9039394948aefedb75603f3c0fa313bae417d40b",
            "2e57b0fe4c8edf090d72d016d19b84ac3573c5ae271dbd5ee0edc2d99ce12110",
            "a6196881e88c441624b36bfa0f4600972fe5dd3609a054925c1c8d6188b9a019",
            "dc53d57e4676dbb6c99737cc6913650c7a015eb63d5ee174d3a82fc4cba80f2a",
            "2020202020202020",
            "deaf59c9d30c11c5738186c3bdbe527869171b250c2ed1779f528e9b0e7d015d",
            "56bcd34170c3b96001f8885abe5fc951a0c4cc1d6e85b20f829f1fa997ba611d",
            "ec6707d6b01580154da2781495a214d45fddd40ebcc4e1b35ecc630c1ebe7346",
            "d6f7d2caea6e7a9e5c52b800b1fb0191790266d35cdc2713cf1343ed4c96711d",
            "f2fbb75af7f1ea9dcd9fb1558a1906f657a2aca7f97a7092033b166d0008a40e",
            "f4fd16969911e9f522cb6c37fbd5e2be08458a55116563a22cb9bd99af551d0f",
            "6afe22eaa78999cc201f7505f5e55d7915f7d76da1687d3825c6f6f37140ab08",
            "70d82a2c3a58739df855084d6baeb0164292555c1185aa8a00ede2a3ed85637f",
            "04ba9d0a1485e04798946cccdc4307931b07f9ab12501bd76f2884a6a1da0938",
            "8aa62f79f87611b768d714670fad98953196a4290f830161ee4908f3f742e842",
            "603b1e3f436f28618ae1b36dcb192550b93801fc4780ecc89bfc76f7e8ecf900",
            "ba01e6b03e009f921eb001494ff65cdf8b90bdd81f52567a6a526bc4c882677f",
            "8e5f5e454bcaa33e85e4c6489811f9a2b565876208bae878136e0a697b8be951",
            "b0aaf77ef25dc3a29a48f0a2f4aa3cdb4b4dbebf04c6205dedefe86189409b0c",
            "8aa86f4321ddc24a17bb6193ebfa8617eb7de69cd3e7d5e0cd9dcd3da099a642",
            "4c473de0bd7e2a11e7b251fa81a936b0232625898c0e8e1c95ba1db7dfc53844",
            "66f078251a6ec3085277720a0d559e90f67cccd52cef55bdd522e5f424026460",
            "22bc40a5f6585b52ddb44a45f4617543b444ee0cb8771746352a7a85512bdb53",
            "d2ec003979559f5bc389c12e7acb6fa80d1a97bbe9349322b04ec7b158cab13c",
            "6a038e79fc5a9ca46e0ae6f372bbd26008904078d2b722f07b60718801d5b32c",
            "f4f06a4da076e1e1a9fefeed6b75cd69d53cc8c7bef54cb8dcc6885df7049a39",
            "9a72936c9ca80fd8232e953f6e54ba84018c10e142b15ab32593f44821a3fc0d",
            "42eaf0ea920d897c30e7d853b818a57fc1d3c97b1ed33e5fb8cd9b97706bd361",
            "a8b6cdecfc711505dcb8383eeb8fb3df0af310741e116676f113c86db1cf6c07",
            "4ee5835aa263322fa24081745b33d7ce09a0841488941efff45da0f68cbe210d",
        ]
    },
    {
        "ix": ix.VerifyGroupedCiphertext2HandlesValidity,
        "cu": 6_400,
        "data": [
            "be62251c7add74d775e10bf73f2b0ec9b9c90402fafa0ebd852f71fedd455362", # context
            "3645c13036eeaf849cb60fef10d68e4a1cd75ae24a3349ba856ae03066ec2330",
            "be0f4307defa2df4333eae951deac2a1e8c2e486f9974bb19acd6f727ab9693b",
            "942d695f6faded93be0ce6be58011416b0b7f78b872781e78b10f1ed8a0bcd6c",
            "5c46ec3e2cbf74dc2e1676ecf7bad5184dd64d67b6bb839330200f880d828673",
            "0007dca6dd7e48f5b4065f37d099025d446e0de24a8890f861892522a4a69e61", # proof
            "30007df0f98bf353173121c371756767da8b05d18e1ae607f47a92cdc3253108",
            "9257a74e93503a07617b702faaff558c40a2d480a96ea26c4e9f1573c430eb5d",
            "01a1f3c59403042008a197914902145470af007509a9c4261535db407f91f30d",
            "bfb586be5dea7f9e40315db6c111f35c1d44af7d878ac99cae03a3d166c1c40f",
        ]
    },
    {
        "ix": ix.VerifyBatchedGroupedCiphertext2HandlesValidity,
        "cu": 13_000,
        "data": [
            "60612761dd6a8f1ed24bd67876dd6049c8b467095de391f4ece89e4f92b84e06", # context
            "628411b120cc9b6511da50016bcba22b578ea20015b76d4e2c8ddce4f5bfe875",
            "6c3234003259908268ffec19643c8dd9c25f576256167ed43320f7eac30b4176",
            "48c55b4be6d7a6c2eb607e7dadfce1a393cee5b776d48a8bd72451cbe9518b56",
            "36e7da51534c344c985cead2745885c8256312f6fca91194d744cd888902c57a",
            "82f9bfcce4e3d22bcec6590588796774f42c4f43562959eab0a3ef9db5661861",
            "80e3f0fc3faae381747ff912ab160401dbed49487103e2933b3f5fc8895b5a7c",
            "20cefb7f025fff1f0c24d04323ed3379c7876f7227be59afdaced91c19eff16b",
            "aa1c9e26986cd4b5001a32f7bf050091084d98f7c44c54649e7f3e7e51b6ae3c", # proof
            "0896653095838a68539ee8d4a80260ef28a64c258bea5365f93a4bc1c1c85045",
            "64ed2adabc59b1efbb4c86837084568996516492809017837eb4aa3e5e36bd2b",
            "4206231378561cf497c190c3138c0c3b5a5385e09d04589b9374bb8e233bec0f",
            "f12b1058acc6e88673575065feaa1f5fc0f010c99dc0e4670643b1fc35155504",
        ]
    },
    {
        "ix": ix.VerifyGroupedCiphertext3HandlesValidity,
        "cu": 8_100,
        "data": [
            "2c1e381203cfa2bb3b964e2863776aaf30176afc57e101c1ea8f0eb0f8cc5d5d", # context
            "485a15910b4882e8108d3e7266ece60a152fe7007d16d2c85d0f8514e743d825",
            "76385ddba81d932da799ddea964f9ae68628449c3f4bb802f998ddbc2797a978",
            "001ac6fb636a66d9ec677fbb58dab15a9889de74c76a32bfe82fc66ad4655a62",
            "8a2ee1fb2c06a91b1ef94f1907f2470833d076ae3b00f40da90286263a208073",
            "18053754653815c3f55c05e78bb5df7a98f99d112e7492460703f375d4b69629",
            "1ce7670beefb038eeeecdd4ad4a449428c4696fc00de63cdec5352e97f531267",
            "7a9c1b463cc73ce83b635f58de5945bac4bfda10ec5bfb579674f2e083918d19", # proof
            "f00cd2eff5cf88d18b9a6959a3ab59b305264d84bd84be735608d12e42f5a25a",
            "78fa7d7ef8294d4f8c4931dcc94dc7c1f38982166b2a1cf2f170a3134fb8601b",
            "def50033244acb0eb0872f64435cfd69735e6812e0ae9cae7aa3bbad88382136",
            "60fc5981df779d3e4e35e2a96a0b90786703fd4fa933298ee01d2e5dfe165c04",
            "fc109d335735d894d2a18fdf5d68b710dd42d2e669671b0bceb5d62b16368e09",
        ]
    },
    {
        "ix": ix.VerifyBatchedGroupedCiphertext3HandlesValidity,
        "cu": 16_400,
        "data": [
            "fe2c3db3f7a880950e51b7a9af3f3be489674d09f85dcb03fac06d99b2672b36", # context
            "ae3be9774285cbec5b1b0abf3cff387d501a3224920b32eeef8a7c4e725a9414",
            "2e3b971852aec1c512f405d125a13f19b3402a658e0e59cdcfad10d01a5c4042",
            "6610b6ef18ca43f9f285320ab8c5c989a51f725f501ead595fa63a541c348514",
            "f47d7f37dfe5dbe69411cfe5f2521b38cc4a5d1563a3f365ac5f448c95a9ff67",
            "be518314bb748d40c4dc8672e43e78916455d7541d8d20fc363c8b8cc614f716",
            "8e4036d7b6955a44ed657b1ed8b9609e3d231622d6ac90844dfa93945f67c11e",
            "54559217a22359e3145beceb6432312e5a0b957cd0099558b8533e99aabd9916",
            "0eee829d7dce7911d2c3b832f07ca53deb65380df73d757eb093c13e9e9aad26",
            "88b8ff8e1a02fdbf61768dbd9aba4e9f14d669a168d0c77ba181be327792534e",
            "8a3f47dca830330c97728812bdc8b66a1c057e8804301c7705d0b83a78e90f66",
            "120b16282af1c2c1a3ded5bdf09fe5309b740c48e7e93c742ec49bf2e4ebbc36", # proof
            "6cc720b5aa33e6951f95138e5808853f178cf8f4d96d749083b41536b226f302",
            "a8d52b600177636ae3c9baf0b400fdbf534d7ebdcb9ab4b247c7cafc45c4a60c",
            "8407a35f0496ac37c048e39bd5a6f51575d49c8e46c1584586b032a2820a4b06",
            "9952beff7a02bc2fc00c4657d960a6a3b40ea79d71a62bf74971cd2c87bf1e0a",
            "479d96f9dfa7c96f46f789e099d875fa505b9228c2d0e915e361c39556f1190f",
        ]
    },
]
for test in test_vectors_agave:
    test["data"] = base64.b16decode(''.join(test.get("data")), True)

# test cases for close_context_state ix
test_vectors_close = [
    {
        # success
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "00"
                ],
                "is_writable": True,
            },
            {
                # destination
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                # "is_writable": True,
                "is_signer": True,
            },
        ],
    },
    {
        # success
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "ff"
                ],
                "is_writable": True,
            },
            {
                # destination + owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                "is_writable": True,
                "is_signer": True,
            },
        ],
        "instr_accounts": [0, 1, 1],
    },
    {
        # success with unnecessary data
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
            "00ff",
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "00"
                ],
                "is_writable": True,
            },
            {
                # destination
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                "is_signer": True,
            },
        ],
    },
    {
        # invalid proof account's owner
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                # "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "00"
                ],
                "is_writable": True,
            },
            {
                # destination
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                "is_signer": True,
            },
        ],
    },
    {
        # missing signature
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L136
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "01"
                ],
                "is_writable": True,
            },
            {
                # destination
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                # "is_signer": True,
            },
        ],
    },
    {
        # dest == proof
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L148
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof == dest
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "01"
                ],
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                "is_signer": True,
            },
        ],
        "instr_accounts": [0, 0, 1],
    },
    {
        # invalid ProofContextStateMeta
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L153-L154
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    # "01"
                ],
                "is_writable": True,
            },
            {
                # destination
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                "is_signer": True,
            },
        ],
    },
    {
        # invalid owner
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L158
        "ix": ix.CloseContextState,
        "cu": 3300,
        "data": [
        ],
        "accounts": [
            {
                # proof
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "lamports": 12345,
                "data": [
                    "ff5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb",
                    "01"
                ],
                "is_writable": True,
            },
            {
                # destination
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "is_writable": True,
            },
            {
                # owner
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
                "is_signer": True,
            },
        ],
    },
]
for test in test_vectors_close:
    test["data"] = base64.b16decode(''.join(test.get("data", [])), True)
    for account in test["accounts"]:
        account["data"] = base64.b16decode(''.join(account.get("data", [])), True)

test_vectors_cu = [
    {
        "ix": ix.CloseContextState,
        "cu": 3300 - 1,
        "data": bytes([])
    },
]
for test in test_vectors_agave:
    new_test = test.copy()
    new_test["cu"] = new_test.get("cu") - 1
    test_vectors_cu.append(new_test)

# failure tests because ctx is invalid
test_vectors_ctx = []
for test in test_vectors_agave:
    new_test = test.copy()
    data = new_test.get("data")
    if len(data) > 0:
        new_test["data"] = bytes([(data[0] + 1)]) + bytes(data[1:])  # modify context
    test_vectors_ctx.append(new_test)

# failure tests because zkp is invalid
test_vectors_proof = []
for test in test_vectors_agave:
    new_test = test.copy()
    data = new_test.get("data")
    if len(data) > 0:
        new_test["data"] = bytes(data[:-1]) + bytes([(data[-1] + 1)])  # modify proof
    test_vectors_proof.append(new_test)

# success tests where proof_data is read from an account
test_vectors_account = []
for test in test_vectors_agave:
    new_test = test.copy()
    new_test["accounts"] = [{
        "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
        "data": test.get("data"),
    }]
    new_test["data"] = bytes([0]*4) # offset in account data
    test_vectors_account.append(new_test)

# success tests where ctx is written in an account
test_vectors_write = []
for test in test_vectors_agave:
    new_test = test.copy()
    ctx_state_len = 33 + CTX_STATE_LEN[test.get("ix").value[0]]
    new_test["accounts"] = [{
        "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
        "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
        "data": bytes([0]*ctx_state_len),
        "is_writable": True,
    }, {
        "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
    }]
    test_vectors_write.append(new_test)

# success tests where proof_data is read from an account and ctx is written in an account
test_vectors_account_write = []
for test in test_vectors_agave:
    new_test = test.copy()
    ctx_state_len = 33 + CTX_STATE_LEN[test.get("ix").value[0]]
    new_test["accounts"] = [{
        "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
        "data": test.get("data"),
    }, {
        "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
        "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
        "data": bytes([0]*ctx_state_len),
        "is_writable": True,
    }, {
        "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
    }]
    new_test["data"] = bytes([0]*4) # offset in account data
    test_vectors_account_write.append(new_test)

# test cases for process_verify_proof workflow
# we use VerifyZeroCiphertext as an example of ZKP
test_vectors_verify = [
    # Part I. Verify ZKP.

    # Case 1. Proof data from account data.
    # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L45-L76
    {
        # success
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
        # [
        #     "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
        #     "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
        #     "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
        #     "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
        #     "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
        #     "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        # ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                ],
            }, {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            }, {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            },
        ],
    },
    {
        # fail - empty data => proof_data from ix => invalid instr data
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L81
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [],
    },
    {
        # fail - proof_data from account, no accounts
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L46-L47
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
    },
    {
        # fail - proof_data from account, account with no data
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L65
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
            }
        ],
    },
    {
        # fail - proof_data from account, account with not enough data
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L65
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    # "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                ],
            }
        ],
    },
    {
        # success - proof_data from account, account with extra data
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f", # extra
                ],
            }
        ],
    },
    {
        # success - proof_data from account, offset
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "20000000",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f", # extra
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f", # extra
                ],
            }
        ],
    },
    {
        # success - proof_data from account, offset
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L65
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "ffffffff",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f", # extra
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f", # extra
                ],
            }
        ],
    },
    # Case 2. Proof data from ix data.
    # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L77-L89
    # Most cases are already covered by previous tests.
    {
        # fail - too much data in account is ok, but in ix fails
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f", # extra
        ],
    },


    # Part II. Store context data.
    {
        # fail - no accounts
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L92-L98
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": []
    },
    {
        # fail - missing one account
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L92-L98
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
            },
        ],
    },
    {
        # fail - no(t enough) accounts
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L92-L98
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                ],
            },
        ],
    },
    {
        # fail - missing one account
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L100-L101
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "00000000",
        ],
        "accounts": [
            {
                "address": base64.b16decode("246965896e3577be29b6edcd2b9a986539ce7a5478e89a029067e3f999b23fb5", True),
                "data": [
                    "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
                    "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
                    "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
                    "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
                    "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
                    "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
                ],
            },
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
            },
        ],
    },
    {
        # fail - read only account + wrong owner + wrong data
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L103-L105
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                # "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                # "data": [
                #     "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                #     "0000000000000000000000000000000000000000000000000000000000000000", # context
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                # ],
                # "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - read only account + wrong owner
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L103-L105
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                # "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                # "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - read only account + wrong data
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                # "data": [
                #     "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                #     "0000000000000000000000000000000000000000000000000000000000000000", # context
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                # ],
                # "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong owner + wrong data
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L103-L105
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                # "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                # "data": [
                #     "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                #     "0000000000000000000000000000000000000000000000000000000000000000", # context
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                # ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - read only account
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L121
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                # "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong owner
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L103-L105
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                # "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong data: empty
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L117-L119
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                # "data": [
                #     "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                #     "0000000000000000000000000000000000000000000000000000000000000000", # context
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                #     "0000000000000000000000000000000000000000000000000000000000000000",
                # ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong data: too small
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L117-L119
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    # "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong data: too large
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L117-L119
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000", # extra
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong data: initialized
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L110-L112
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000001", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # fail - wrong data: initialized (invalid proof type)
        # https://github.com/anza-xyz/agave/blob/v2.0.1/programs/zk-elgamal-proof/src/lib.rs#L110-L112
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "0000000000000000000000000000000000000000000000000000000000000000ff", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # success - wrong data: dirty (1)
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "010000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0000000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
    {
        # success - wrong data: dirty (2)
        "ix": ix.VerifyZeroCiphertext,
        "cu": 6_000,
        "data": [
            "e849bc396675d659c14fd2e0619abd9124bf1be40f3ef0e9b81cfe87e3e16b35", # context
            "7670194b708b5728e62b5bdac8fe672b13d378b746e7630c12f13cac3c179e26",
            "c883cc653e0737f7c866596d739ed3cfa3dcae9f4ce87306998e44ec4a073360",
            "6467faff06ec0729956a25a76fd0af5219305cc6a963707928af35c29db13d2f", # proof
            "1ca133e5e58bcd46eb4927d55f487d98f6b6d3ce0a73c84be7084233f71ab864",
            "572e427f0f5a41d2ea66b90d07e3ab5ad9a2e3ba8b391b2eceec38e5a0e0650f",
        ],
        "accounts": [
            {
                "address": base64.b16decode("86ddc6585609faef7c746983e0b198e432e9d1771d615ce2406e320c779f4a3d", True),
                "owner": fd58.dec32(bytes("ZkE1Gama1Proof11111111111111111111111111111", "utf-8")),
                "data": [
                    "000000000000000000000000000000000000000000000000000000000000000000", # authority + proof
                    "0100000000000000000000000000000000000000000000000000000000000000", # context
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ],
                "is_writable": True,
            },
            {
                "address": base64.b16decode("be5b54cdb01762497c7fd98bfcaaec1d2a2cad1c2bb5134857b68f0214935ebb", True),
            }
        ],
    },
]
for test in test_vectors_verify:
    test["data"] = base64.b16decode(''.join(test.get("data", [])), True)
    for account in test.get("accounts", []):
        account["data"] = base64.b16decode(''.join(account.get("data", [])), True)

def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), test) for j, test in enumerate(test_vectors)]


print("Generating zk-sdk tests...")

test_vectors = _into_key_data("a", test_vectors_agave) \
    + _into_key_data("cu", test_vectors_cu) \
    + _into_key_data("c", test_vectors_ctx) \
    + _into_key_data("p", test_vectors_proof) \
    + _into_key_data("acc", test_vectors_account) \
    + _into_key_data("w", test_vectors_write) \
    + _into_key_data("wacc", test_vectors_account_write) \
    + _into_key_data("close", test_vectors_close) \
    + _into_key_data("verif", test_vectors_verify)

program_id = fd58.dec32(bytes(program_id, "utf-8"))
program_owner = fd58.dec32(
    bytes("NativeLoader1111111111111111111111111111111", "utf-8")
)
for key, test in test_vectors:
    instr_ctx = invoke_pb.InstrContext()
    instr_ctx.program_id = program_id
    instr_ctx.data = bytes(test.get("ix").value) + test.get("data")
    instr_ctx.cu_avail = test.get("cu")

    accounts = []
    test_accounts = test.get("accounts", [])
    for account in test_accounts:
        # account
        acc = context_pb.AcctState()
        acc.address = account.get("address")
        acc.owner = account.get("owner", bytes([0]*32))
        acc.lamports = account.get("lamports", 0)
        acc.data = account.get("data", bytes([]))
        accounts.append(acc)

    instr_accounts = []
    test_instr_accounts = test.get("instr_accounts", range(len(accounts)))
    for j in test_instr_accounts:
        # instr account
        instr_acc = invoke_pb.InstrAcct()
        instr_acc.index = j
        account = test_accounts[j]
        instr_acc.is_writable = account.get("is_writable", False)
        instr_acc.is_signer = account.get("is_signer", False)
        instr_accounts.append(instr_acc)

    # program account
    program_account = context_pb.AcctState()
    program_account.address = program_id
    program_account.owner = program_owner
    accounts.append(program_account)

    instr_ctx.accounts.extend(accounts)
    instr_ctx.instr_accounts.extend(instr_accounts)
    instr_ctx.epoch_context.features.features.extend([0x8e1411a93085cb0e])

    serialized_instr = instr_ctx.SerializeToString(deterministic=True)
    filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
    with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
        f.write(serialized_instr)

print("done!")
