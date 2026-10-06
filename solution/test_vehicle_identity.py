from vehicle_identity import extract_vehicle_identity


examples = [
    "FORD F-600 ESTACAS TANDEM HASTA 16 TON.",
    "DODGE RAM 2500 QUAD CAB SLT. 4X2",
    "DODGE RAM 4000 CHASIS CABINA STD.",
    "TOYOTA TACOMA",
    "HINO 816 LONG SERIE 300",
    "HONDA CR-V EX PREMIUM 2.4",
]


for description in examples:

    result = extract_vehicle_identity(description)

    print(
        description,
        "=>",
        result,
    )