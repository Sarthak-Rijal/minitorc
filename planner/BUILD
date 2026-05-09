py_library(
    name = "planner",
    srcs = ["planner.py"],
    deps = ["//perception:detector"],
    visibility = ["//visibility:public"],
)

py_test(
    name = "planner_test",
    srcs = ["planner_test.py"],
    deps = [
        ":planner",
        "//perception:detector",
    ],
)
