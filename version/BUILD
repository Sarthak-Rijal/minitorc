genrule(
    name = "version",
    outs = ["version.py"],
    stamp = True,
    cmd = """
        commit=$$(grep ^STABLE_GIT_COMMIT bazel-out/stable-status.txt | awk '{print $$2}' || echo unknown);
        timestamp=$$(grep ^BUILD_TIMESTAMP bazel-out/volatile-status.txt | awk '{print $$2}' || echo unknown);
        echo "GIT_COMMIT = '$$commit'" > $@
        echo "BUILD_TIMESTAMP = '$$timestamp'" >> $@
    """,
    visibility = ["//visibility:public"],
)
