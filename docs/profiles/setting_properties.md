Setting Properties
====
Each setting in Cura has a number of properties. It's not just a key and a value. This page lists the properties that a setting can define.

* `key` (string): __The identifier by which the setting is referenced.__  
   * This is not a human-readable name, but just a reference string, such as `layer_height_0`. 
   * This is not actually a real property but just an identifier; it can't be changed. 
   * Typically these are named with the most significant category first, in order to sort them better, such as `material_print_temperature`.  
* `value` (optional): __The current value of the setting.__  
  * This can be a function (an arbitrary Python expression) that depends on the values of other settings.  
  * If it's not present, the `default_value` is used.
* `default_value`: __A default value for the setting if `value` is undefined.__  
  * This property is required.  
  * It can't be a Python expression, but it can be any JSON type.  
  * This is made separate so that CuraEngine can read it out for its debugging mode via the command line, without needing a complete Python interpreter.
* `label` (string): __The human-readable name for the setting.__  
  * This label is translated.
* `description` (string): __A longer description of what the setting does when you change it.__  
  * This description is translated.
* `type` (string): __The type of value that this setting contains.__  
  * Allowed types are: `bool`, `str`, `float`, `int`, `enum`, `category`, `[int]`, `vec3`, `polygon` and `polygons`.
* `unit` (optional string): __A unit that is displayed at the right-hand side of the text field where the user enters the setting value.__
* `resolve` (optional string): __A Python expression that resolves disagreements for global settings if multiple per-extruder profiles define different values for a setting.__  
  * Typically this takes the values for the setting from all stacks and computes one final value for it that will be used for the global setting. For instance, the `resolve` function for the build plate temperature is `max(extruderValues('material_bed_temperature')`, meaning that it will use the hottest bed temperature of all materials of the extruders in use.
* `limit_to_extruder` (optional): __A Python expression that indicates which extruder a setting will be obtained from.__  
  * This is used for settings that may be extruder-specific but the extruder is not necessarily the current extruder. For instance, support settings need to be evaluated for the support extruder. Infill settings need to be evaluated for the infill extruder if the infill extruder is changed.
* `enabled` (optional string or boolean): __Whether the setting can currently be made visible for the user.__  
  * This can be a simple true/false, or a Python expression that depends on other settings.  
  * Typically used for settings that don't apply when another setting is disabled, such as to hide the support settings if support is disabled.
* `minimum_value` (optional): __The lowest acceptable value for this setting.__  
  * If it's any lower, Cura will not allow the user to slice.  
  * This property only applies to numerical settings.
  * By convention this is used to prevent setting values that are technically or physically impossible, such as a layer height of 0mm.  
* `maximum_value` (optional): __The highest acceptable value for this setting.__  
  * If it's any higher, Cura will not allow the user to slice.  
  * This property only applies to numerical settings.
  * By convention this is used to prevent setting values that are technically or physically impossible, such as a support overhang angle of more than 90 degrees.   
* `minimum_value_warning` (optional): __The threshold under which a warning is displayed to the user.__  
  * This property only applies to numerical settings.
  * By convention this is used to indicate that it will probably not print very nicely with such a low setting value.   
* `maximum_value_warning` (optional): __The threshold above which a warning is displayed to the user.__
  * This property only applies to numerical settings.  
  * By convention this is used to indicate that it will probably not print very nicely with such a high setting value.   
* `settable_globally` (optional boolean): __Whether the setting can be changed globally.__  
  * For some mesh-type settings such as `support_mesh` this doesn't make sense, so those can't be changed globally. They are not displayed in the main settings list then.
* `settable_per_meshgroup` (optional boolean): __Whether a setting can be changed per group of meshes.__  
  * *This is currently unused by Cura.*
* `settable_per_extruder` (optional boolean): __Whether a setting can be changed per extruder.__  
  * Some settings, like the build plate temperature, can't be adjusted separately for each extruder. An icon is shown in the interface to indicate this.  
  * If the user changes these settings they are stored in the global stack.
* `settable_per_mesh` (optional boolean): __Whether a setting can be changed per mesh.__  
  * The settings that can be changed per mesh are shown in the list of available settings in the per-object settings tool.
* `children` (optional list): __A list of child settings.__  
  * These are displayed with an indentation. If all child settings are overridden by the user, the parent setting gets greyed out to indicate that the parent setting has no effect any more. This is not strictly always the case though, because that would depend on the inheritance functions in the `value`.
* `icon` (optional string): __A path to an icon to be displayed.__  
  * Only applies to setting categories.
* `allow_empty` (optional bool): __Whether the setting is allowed to be empty.__ 
   * If it's not, this will be treated as a setting error and Cura will not allow the user to slice.  
   * Only applies to string-type settings.
* `warning_description` (optional string): __A warning message to display when the setting has a warning value.__  
  * *This is currently unused by Cura.*
* `error_description` (optional string): __An error message to display when the setting has an error value.__  
  * *This is currently unused by Cura.*
* `options` (dictionary): __A list of values that the user can choose from.__  
  * The keys of this dictionary are keys that CuraEngine identifies the option with.  
  * The values are human-readable strings and will be translated.  
  * Only applies to (and only required for) enum-type settings.
* `comments` (optional string): __Comments to other programmers about the setting.__  
  * *This is currently unused by Cura.*
* `is_uuid` (optional boolean): __Whether or not this setting indicates a UUID-4.__  
  * If it is, the setting will indicate an error if it's not in the correct format.  
  * Only applies to string-type settings.
* `regex_blacklist_pattern` (optional string): __A regular expression, where if the setting value matches with this regular expression, it gets an error state.__  
  * Only applies to string-type settings.
* `error_value` (optional): __If the setting value is equal to this value, it will show a setting error.__  
  * This is used to display errors for non-numerical settings such as checkboxes.
* `warning_value` (optional): __If the setting value is equal to this value, it will show a setting warning.__  
  * This is used to display warnings for non-numerical settings such as checkboxes.
