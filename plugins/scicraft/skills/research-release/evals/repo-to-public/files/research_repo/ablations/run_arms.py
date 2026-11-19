from fieldnet.model import FieldNet
for act in ["relu", "tanh", "none"]:
    for v in ["A", "B"]:
        print(act, v, FieldNet(4, act=act, mix_variant=v))
