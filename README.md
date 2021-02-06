# source-restore
A python script to restore a provided list of source files given specific git repos and versions. Inspired by npm. Built to manage dependencies for arduino when multiple projects exist with separate dependencies and versions. This allows you to have a arduino project given a simple makefile plus your source code and build a development pipeline where separate environments including a build server can simply restore dependencies including the arduino core and run with it.

# Features
 - Clones by branch, version, or tag.
 - Allows for running a post-restore command.
 - Configurable destination for restored packages.
 - Saves restore results to the destination directory so restore only occurs when the specified version per package is not currently present.

# Use
### To run:
`$ ./source-restore.py -f path/to/packages.json [options]`

### Options
|Parameter|Description|Default|
|---|---|---|
|-f, --file|The json file to use as your packages definition.||
|-o, --output|The destination directory for all source packages to be restored to.|./packages|

### Packages Json File
See examples folder for example package json files.

#### Example:
```json
{
    "sources": [
        {
            "name": "NameOfDependency",
            "repo": "https://github.com/repo/path",
            "version": "VersionOrCommit",
            "postRestore": {
                "shell": "shell command to run after successful clone",
                "cwd": "/the/directory/to/run/shell/command"
            }
        },
        ...
    ]
}
```
#### Source Definition:
|Parameter|Description|Default|
|---|---|---|
|name|The name of the dependency. This is used as the name of the resulting directory that the repo is cloned into.||
|repo|The url of the git repo to clone.||
|version|The branch, tag, or commit ID to clone.||
|postRestore.shell|The shell command to run once after a successful git clone.||
|postRestore.cwd|The current working directory to provide to the shell command. Defaults to the cloned directory for the source. A relative path given here gets joined to the cloned directory allowing you to jump around relative to the cloned repo.|{destinationDirectory}/{name}/

### Output Directory Example
```
/path/to/output/directory
├── Dependency1
|   └── ClonedContents1
├── Dependency2
|   └── ClonedContents2
├── Dependency3
|   └── ClonedContents3
└── .restoreResults.json
```