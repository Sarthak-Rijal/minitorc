py_library(
    name = "validator",
    srcs = ["validator.py"],
    deps = 
    [
        "//perception:detector",
        "//planner:planner"
    ],
    visibility = ["//visibility:public"],
)


py_test(
    name = "validator_test",
    srcs = ["validator_test.py"],
    deps = [":validator","//perception:detector", "//planner:planner"],
)
