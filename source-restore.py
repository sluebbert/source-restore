#!/usr/bin/python

import argparse
import json
import subprocess
from sys import stdout, stderr
from os import path, mkdir
from shutil import rmtree

def printError(message):
	stderr.write("\033[38;5;9m" + message + "\033[0m\n\n")

def getSourceDefinitions(file):
	try:
		with open(file, 'r') as f:
			return json.load(f)
	except Exception as err:
		printError("An error occurred while parsing the provided json file: " + str(err))
		return None

def getRestoreResults(resultFile):
	try:
		if not path.exists(resultFile):
			return {"sources": {}}
		with open(resultFile, 'r') as f:
			return json.load(f)
	except Exception as err:
		printError("An error occurred while parsing the provided json file: " + str(err))
		return {"sources": {}}

def saveRestoreResults(resultFile, results):
	with open(resultFile, 'w') as f:
		return json.dump(results, f, indent=True)

def cleanseRestoreResults(results, existingKeys):
	previousKeys = [x for x in restoreResults["sources"]]
	for repoName in previousKeys:
		if repoName not in existingKeys:
			restoreResults["sources"].pop(repoName, None)

def enforceDefinition(definition, restoreResults, outputDirectory):
	output = None

	try:
		name = definition["name"]
		repo = definition["repo"]
		version = definition["version"]
		postRestore = definition["postRestore"] if "postRestore" in definition else None
		previousResult = restoreResults['sources'][name] if name in restoreResults['sources'] else None

		if previousResult is not None and "version" in previousResult and previousResult["version"] == version:
			return

		print("Restoring %s %s %s" % (name, repo, version))
		output = path.join(outputDirectory, name)
		
		if path.exists(output):
			rmtree(output)

		# Try to clone branch
		stdout.write('\trestoring...')
		stdout.flush()
		process = subprocess.Popen(['git', 'clone', '--depth', '1', '-q', '--branch', version, repo, output], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
		process.wait()
		if process.returncode != 0:
			if path.exists(output):
				rmtree(output)
			
			# Failed so lets just straight clone
			process = subprocess.Popen(['git', 'clone', '-q', repo, output], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
			process.wait()
			if process.returncode == 0:
				# Now that we have our clone, lets checkout a specific revision
				process = subprocess.Popen(['git', 'checkout', version], cwd=output, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
				process.wait()
				if process.returncode != 0:
					raise Exception("Failed to checkout version %s from cloned repo.\n%s" % (version, process.stderr.read()))
			else:
				raise Exception("Failed to clone repo.\n%s" % (process.stderr.read()))
		stdout.write('\n\t done.\n')
		stdout.flush()

		if postRestore is not None:
			stdout.write('\trunning post restore command...\n')
			stdout.flush()

			shellCommand = postRestore["shell"]
			cwd = postRestore["cwd"] if "cwd" in postRestore else None
			if cwd is None:
				cwd = output
			else:
				cwd = path.join(output, cwd)

			process = subprocess.Popen(shellCommand, shell=True, cwd=cwd)
			process.wait()
			if process.returncode != 0:
				raise Exception("Failed to run post restore command.")
			stdout.write('\n\t done.\n')
			stdout.flush()

		restoreResults["sources"][name] = {
			"status": "success",
			"repo": repo,
			"version": version
		}

	except Exception as err:
		printError("\nAn error occurred while restoring %s: %s" % (name, str(err)))
		restoreResults["sources"][name] = {"status": "failed"}
		if output is not None and path.exists(output):
			rmtree(output)

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Pulls source repos.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-f', '--file', help='The json file containing sources to restore.', required=True)
	parser.add_argument('-o', '--output', default='./packages', help='The output directory to restore sources to.')

	args = parser.parse_args()

	if not path.exists(args.output):
		mkdir(args.output)

	resultFile = path.join(args.output, ".restoreResults.json")
	sources = getSourceDefinitions(args.file)
	restoreResults = getRestoreResults(resultFile)

	existingKeys = []
	for definition in sources["sources"]:
		existingKeys.append(definition["name"])
		enforceDefinition(definition, restoreResults, args.output)

	cleanseRestoreResults(restoreResults, existingKeys)
	saveRestoreResults(resultFile, restoreResults)
