#  SmartSlice UI  (Source Tree)

#### Sub-Directory Contents
*  **SmartSliceExtension:**  Post-Staging, High-Level Operations
*  **SmartSliceStage:**  Staging Operations
*  **SmartSliceSelection:**  Selection Tool Operations
*  **SmartSliceConstraints:**  Load/Anchor Operations


####  Sub-Plugin Load Order

* *SmartSliceExtension* calls initialization (Staging) operations within *SmartSliceStage*
* *SmartSliceStage* calls initialization operations for each plugin-specific tool in following order
    * *SmartSliceSelection*
    * *SmartSliceConstraints*
    * *SmartSliceJobs*
* After staging initalization concludes, functionality is called on event-driven framework

