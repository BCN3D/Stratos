from enum import Enum

class SmartSliceCloudStatus(Enum):
    NoConnection = 1
    BadLogin = 2
    Cancelling = 3
    Errors = 4
    ReadyToVerify = 5
    Underdimensioned = 6
    Overdimensioned = 7
    BusyValidating = 8
    BusyOptimizing = 9
    Optimized = 10
    RemoveModMesh = 11
    Queued = 12

    @staticmethod
    def optimizable():
        return (
            SmartSliceCloudStatus.Underdimensioned,
            SmartSliceCloudStatus.Overdimensioned,
            SmartSliceCloudStatus.RemoveModMesh
        )

    @staticmethod
    def busy():
        return SmartSliceCloudStatus.BusyValidating, SmartSliceCloudStatus.BusyOptimizing, SmartSliceCloudStatus.Queued

