import re
import json
import glob
import inspect
import typing

# Source language used by the calling script for translatable strings. This should always be set.
__source_lang = None

# Target language to translate to. If this is the same as source_lang or is None,
# the module will function as a passthrough and not translate anything.
__target_lang = None

# A dictionary to store loaded translation data. It will be populated by __load_translations(),
# which is called by various functions in this module as needed. Data structure is as follows:
# {"Source phrase in source language" : "Translated version of source phrase"}
__translations: typing.Dict[str, str] = {}

# A function to load a translation file from the source directory. A target_lang
# must always be passed, as it will define the name of the file to be searched
# for by this function--The full name of the file being target_lang + ".translation"
def __load_translations(target_lang):
    
    # In this function we'll need access to the global var "__translations".
    global __translations
    
    # That being done, attempt to find the specified file.
    try:
        
        # This context handler tries to open the specified file, target_lang + ".translation",
        # in the source directory. If successful, it loads the json in that file and stores
        # the resulting dict of translation data to the global var "__translations".
        with open(target_lang+".translation", "r", encoding='utf-8') as read_file:
            __translations = json.load(read_file)
            
    # If a matching filename is not found for the given target_lang,
    except FileNotFoundError:
        # Reraise an error denoting that the requested file is missing.
        raise FileNotFoundError("No translation file found for target language '" + target_lang + "'.")
    
    # If an error occurs parsing the json in the file,
    except json.decoder.JSONDecodeError as err:
        # Reraise an error denoting the problem and its location within the file.
        raise json.decoder.JSONDecodeError("\nCouldn't parse JSON in file '" + target_lang + ".translation'. "
                                            + "Check to make sure it is not malformed.\n"
                                            +"Location of error in JSON data file", err.doc, err.pos)


# The function used by the calling script to initialize the translation functions.
# It will be passed a source_lang and optionally a target_lang, both strings.
# If target_lang is None, the translator will be setup for passthrough of the source lang.

# This function returns a reference to the function __gettext(), which does the actual translating;
# thus when this translator() function is called, its return should be stored to "_" in
# the calling script so translation can be accessed by the call _('Text to be translated.')

def get_lang_readable_name(lang):
    # Note: for english, which we don't expect there to
    # usually be a translation file for, bypass:
    if lang == 'en':
        return "English"
    
    # lang is a required field and must be a str of len 2.
    if type(lang) is not str or len(lang) != 2:
        # If it is not valid, raise a ValueError.
        raise ValueError("source_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Otherwise, if the passed lang is valid,
    else:
        # Backup any current data in __translations so we can
        # restore it at the end of this function.
        global __translations
        temptrans = __translations
        
        # Load translation data for lang:
        __load_translations(lang)
        
        # Get the readable name of the language:
        output = __translations["__target_lang_readable"]
        
        # restore the temporary translation data from earlier to its known good state:
        __translations = temptrans
        
        # Return
        return output
        

def translator(source_lang, target_lang=None):
    
    # Source lang is a required field and must be a str of len 2.
    if type(source_lang) is not str or len(source_lang) != 2:
        # If it is not valid, raise a ValueError.
        raise ValueError("source_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Otherwise, if the passed source_lang is valid,
    else:
        # Store it to the global variable "__source_lang".
        # It is also stored here as lowercase to standardize
        # case for later matching.
        global __source_lang
        __source_lang = source_lang.lower()
    
    # Target language MAY be defined. If it is None, the translation function __gettext()
    # will act as a passthrough, returning the original source language text.
    
    # First, validate the target_lang as we did for the source_lang
    # (the rules are the same, except this time it can also be None).
    
    # Setup the global variable "__target_lang" to receive data,
    # if we should find valid data.
    global __target_lang
    
    # If no target_lang was passed,
    if target_lang is None:
        # set global "__target_name" to None
        __target_lang = None
        
    # If a valid target_lang string was passed,
    elif type(target_lang) == str and len(target_lang) == 2:
        # Store it to global "__target_name"
        # as a lowercase string, as before.
        __target_lang = target_lang.lower()
        
    else:
        # If it is not valid, raise a ValueError.
        raise ValueError("target_lang must be either a two character string, or the value None.")
    
    # Validation of parameters done. 
 
    # Now, if we have a target language to translate to,
    if __target_lang != None and __target_lang != __source_lang:
        
        # attempt to load the translation file. this function will
        # raise an error if the specified file is not found.
        __load_translations(__target_lang)
    
    # If we don't have a target language to translate to,
    else:
        # Reset the global translations dict to empty.
        global __translations
        __translations = {}
    
    # Finally, return the function gettext. It should be assigned in the calling script to "_" so that
    # it can be called from anywhere using "_()"
    return __gettext

# A function to translate text. When the user runs the translator() function,
# a reference to this function is returned such that the user may assign that
# reference to a variable and call it as needed, such as _("text to be translated")
# if the reccomended variable of "_" is used.

# The sole parameter, source_phrase, is the incoming string to be translated
# from __source_lang to __target_lang. It will be looked up in the dict and
# translated on demand, or if no match is found a KeyError will be thrown.
def __gettext(source_phrase):
    
    # First, confirm that we have a valid __source_lang.
    if type(__source_lang) != str or len(__source_lang) != 2:
    
        # If not, raise an error.
        raise RuntimeError("The source language of your script has not been set to valid data. "
                         + "Please make sure it is set in your calling script by first calling "
                         + "the function translator() with a valid source_lang parameter.")
    
    # Next, validate the __target_lang as well.
    if type(__target_lang) not in [str, type(None)] or \
            __target_lang is not None and len(str(__target_lang)) != 2:
        
        # If it is set to invalid data, raise an error stating such.
        raise RuntimeError("The target language of your script has been set to a bad value. "
                         + "Please make sure it is set in your calling script by first calling "
                         + "the function translator() with a valid target_lang parameter, or "
                         + "otherwise setting the target_lang to None.")
    
    # Otherwise, if the data is valid,
    else:
        
        # If setup for passthrough,
        if __target_lang == None or __target_lang == __source_lang:
            
            # Return the string as-is, without translation.
            return source_phrase
        
        # If setup to translate,
        else:
            
            # Check the translation dict for the source_phrase as a key.
            if source_phrase in __translations.keys():
                
                # If found, return the translated phrase.
                return __translations[source_phrase]
            
            # If not found in the dict,
            else:
                
                # Raise an error stating such.
                raise KeyError("Source phrase '" + source_phrase
                               + "' was not found in the translation file for target_lang '"
                               + __target_lang + "'.")


# Function to return what language packs are installed.
# These will be files in the source directory with the extension '.translation'.
def getlangs(source_lang):
    
    # source_lang should be a string and always should be provided to this function.
    if type(source_lang) is not str or len(source_lang) != 2:
        raise ValueError("source_lang must be a string of exactly two characters in length.")
    
    # We always support the source language used in the script itself.
    # Convert it to lowercase, and store it at the top of the list.
    source_lang = source_lang.lower()
    langs = [source_lang]
    
    # Add to this list another list of files with the .translation extension
    # that were found in the source directory.
    langs = langs + glob.glob("*.translation")
    
    # Trim all language strings to 2 characters.
    langs = [lang[:2] for lang in langs]
    
    # save the currently loaded translation data, for restoration later. 
    global __translations
    temptrans = __translations
    
    # Iterate over all found langs to validate their data
    for lang in langs:
        
        # Bypass checks for the source language, as it won't need any translation data loaded.
        if lang == source_lang:
            continue
        
        # For other language packs found in the source directory:
        try:
            
            # try to load the translation file for the current lang.
            __load_translations(lang)
            
            # if that load was successful, confirm its "__source_lang" key matches our source_lang.
            if __translations["__source_lang"].lower() != source_lang:
                
                # If the above validation failed, raise an error.
                raise RuntimeError("The translation file for '" + lang + "' defines a source language of '"
                                   + __translations["__source_lang"].lower() + "' which does not match the "
                                   + "program's specified source language of '" + source_lang + "'.")
        
        # If the load of translation data failed or was invalid:
        except RuntimeError as e:
            
            # Catch and reraise the above mismatched language error if it is what's being excepted:
            if "does not match" in str(e):
                raise e
            
            # If any other error was raised, reraise as a general loading error.
            else:
                raise RuntimeError("Could not load the translation file for '" + lang
                                   + "'. Please check the file for errors.")
        
        # And no matter what happens above, always:
        finally:
            
            # restore the temporary translation data from earlier to its known good state.
            __translations = temptrans
    
    # Lastly, if all langs loaded successfully, return the list of available langs.
    return langs

# Function to generate a skeleton template for translation files.
def get_data_template(source_lang, target_lang):
    # Source lang is a required field and must be a str of len 2.
    if type(source_lang) is not str or len(source_lang) != 2:
        # If it is not valid, raise a ValueError.
        raise ValueError("source_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Otherwise, if the passed source_lang is valid,
    else:
        # Store it to the local variable "__source_lang".
        # It is also stored here as lowercase to standardize
        # case for later matching.
        source_lang = source_lang.lower()
    
    # Next, validate the target_lang as we did for the source_lang.
        
    # If a valid target_lang string was passed,
    if type(target_lang) == str and len(target_lang) == 2:
        # Store it to local "target_name"
        # as a lowercase string, as before.
        target_lang = target_lang.lower()
        
    else:
        # If it is not valid, raise a ValueError.
        raise ValueError("target_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Validation of parameters done.
    
    # Get the source file for the calling script:
    caller = inspect.stack()[1].filename
    
    # Populate required special fields into a dict named data,
    # to which we will also add found translatable strings.
    data = {
        "__source_lang": source_lang,
        "__target_lang": target_lang,
        "__target_lang_readable": ""
        }
    
    # Get the text of the calling file:
    with open(caller, 'r') as file:
        script = file.read()
    
    # Create an iterator to find all matches in the code for the
    # following regex which will match strings formatted as _("Translatable")
    matches = re.finditer(r'^.*_\(["\'](.+?)["\']\).*$', script, re.M)
        
    # Iterate matches,
    for match in matches:
        
        # and if the line is not a comment,
        if re.search(r'^.*#', match.group(0), re.M) is None:
            
            # add the match group to the data dict.
            data.update({match.group(1) : ""})
        
    return json.dumps(data, indent=4)

# Function to cleanup a translation file,
# identifying unused translation data.
def cleanup_translation_data(target_lang):
    # lang is a required field and must be a str of len 2.
    if type(target_lang) is not str or len(target_lang) != 2:
        # If it is not valid, raise a ValueError.
        raise ValueError("target_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Get the filename of the source (calling) script:
    caller = inspect.stack()[1].filename
    
    # Get the text of that file:
    with open(caller, "r") as file:
        script = file.read()
        
    scriptdata = []
    
    # Create an iterator to find all matches in the code for the
    # following regex which will match strings formatted as _("Translatable")
    matches = re.finditer(r'^.*_\(["\'](.+?)["\']\).*$', script, re.M)
        
    # Iterate matches,
    for match in matches:
        
        # and if the line is not a comment,
        if re.search(r'^.*#', match.group(0), re.M) is None:
            
            # add the match group to the scriptdata dict.
            scriptdata = scriptdata + [match.group(1)]
        
    # Before messing with translation data, make a backup:
    global __translations
    transbackup = __translations
    
    # Next, try to load translation data for target_lang
    __load_translations(target_lang)
    
    translationfiledata = list(__translations.keys())
    
    # Create a report to hold found errors:
    report = []
    
    # Iterate over data from translation file
    for phrase in translationfiledata:
        # Ignore special fields
        if phrase[:2] == "__":
            continue
        
        # Check if the phrase exists in the source code
        # as a translatable string
        if phrase not in scriptdata:
            
            # If it doesn't, add it to the report.
            report = report + ["'" + phrase + "' was not found in the source code."]
    
    return "\n".join(report)

# Function to check that all translatable strings in the
# source file have a translation for a given language.
def validate_translation_data(source_lang, target_lang):

    # Source lang is a required field and must be a str of len 2.
    if type(source_lang) is not str or len(source_lang) != 2:
        # If it is not valid, raise a ValueError.
        raise ValueError("source_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Otherwise, if the passed source_lang is valid,
    else:
        # Store it to the local variable "__source_lang".
        # It is also stored here as lowercase to standardize
        # case for later matching.
        source_lang = source_lang.lower()
    
    # Next, validate the target_lang as we did for the source_lang.
        
    # If a valid target_lang string was passed,
    if type(target_lang) == str and len(target_lang) == 2:
        # Store it to local "target_name"
        # as a lowercase string, as before.
        target_lang = target_lang.lower()
        
    else:
        # If it is not valid, raise a ValueError.
        raise ValueError("target_lang must be a two character string, such as 'en' or 'pl'.")
    
    # Validation of parameters done.
    
    # Get the filename of the source (calling) script:
    caller = inspect.stack()[1].filename
    
    # Get the text of that file:
    with open(caller, "r") as file:
        script = file.read()
    
    # Initialize a data dict with the required "__source_lang" and "__target_lang" fields:
    scriptdata = {
        "__source_lang": source_lang,
        "__target_lang": target_lang,
        "__target_lang_readable": ""
        }
    
    # Create an iterator to find all matches in the code for the
    # following regex which will match strings formatted as _("Translatable")
    matches = re.finditer(r'^.*_\(["\'](.+?)["\']\).*$', script, re.M)
        
    # Iterate matches,
    for match in matches:
        
        # and if the line is not a comment,
        if re.search(r'^.*#', match.group(0), re.M) is None:
            
            # add the match group to the scriptdata dict.
            scriptdata.update({match.group(1) : ""})
        
    # Get subset of special keys in dict:
    specialkeys = dict({(key, value) for key, value in scriptdata.items() if key[:2] == "__"})
    
    # Before messing with translation data, make a backup:
    global __translations
    transbackup = __translations
    
    # Next, try to load translation data for target_lang
    __load_translations(target_lang)
    
    # Create variables to hold reports of any missing strings
    # and incomplete/invalid translations found in the file:
    missings: typing.List[str] = []
    incompletes: typing.List[str] = []
    
    # For every translatable key in the source file:
    for key in scriptdata.keys():
        
        # If that key does not exist in the translation file as well,
        if key not in __translations.keys():
            
            # Add it to the missings report.
            missings = missings + ['    "' + key + '": None,\n']
        
        # Otherwise, if the key exists on file but doesn't have a valid translation:
        elif type(__translations[key]) != str or len(__translations[key].strip()) < 1:
            
            # Add it to the incompletes report.
            incompletes = incompletes + ["(!) Source phrase '" + key
                          + "' exists in file but has no valid translation to return."]
        
    # Build the final report of errors, if errors were found:
    if len(incompletes) > 0 or len(missings) > 0:
        
        # Add incompletes to the report.
        report = incompletes
        
        # If there are missings to add,
        if len(missings) > 0:
            
            # Add a header line for missings,
            report = report + ["(!) Source phrase for the following keys does not exist on file:"]
            
            # Then add the missings to the report.
            report = report + missings
        
        # Combine the report (currently a list of strings)
        # into one large string with newline splits.
        report = "\n".join(report)
        
        # As cleanup, if missings were added, trim the last two
        # characters from the report; these will be ",\n" and
        # should be discarded for readability.
        if len(missings) > 0:
            report = report[:-2]
        
        # Finally, with errors found and the report built,
        # Raise it as a warning.
        raise RuntimeWarning("Errors found in translation data:\n" + report)
        
        
    # Before returning from the function,
    # restore the translation data backup to its
    # state before the function was run:
    __translations = transbackup
    
    # Finally, if we made it this far without errors, return a string
    # describing what data was found in the file.
    return "Found " + str(len(scriptdata) - len(specialkeys)) \
           + " unique translatable strings in file, plus " \
           + str(len(specialkeys)) + " special keys. All translation data OK."


