from sea_g2p import SEAPipeline, Normalizer, G2P
import inspect

with open("test_output.txt", "w", encoding="utf-8") as f:
    # Test SEAPipeline.run
    p = SEAPipeline()
    result = p.run("test")
    f.write("SEAPipeline.run: " + repr(result) + "\n")

    # Test Normalizer
    n = Normalizer()
    result = n.normalize("test")
    f.write("Normalizer.normalize: " + repr(result) + "\n")

    # Test G2P
    g = G2P()
    result = g.convert("test")
    f.write("G2P.convert: " + repr(result) + "\n")

    # Check if punc_norm parameter exists
    f.write("\nNormalizer.normalize signature: " + str(inspect.signature(n.normalize)) + "\n")
    f.write("G2P.convert signature: " + str(inspect.signature(g.convert)) + "\n")
    f.write("SEAPipeline.run signature: " + str(inspect.signature(p.run)) + "\n")