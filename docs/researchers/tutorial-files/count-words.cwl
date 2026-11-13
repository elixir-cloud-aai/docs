# Demo workflow of the researcher tutorials of ELIXIR On-Cloud: counts the
# lines, words and characters of a text file, like `wc`
cwlVersion: v1.0
class: CommandLineTool
doc: Counts the lines, words and characters of a text file.
requirements:
  DockerRequirement:
    dockerPull: alpine:3.20
baseCommand: wc
stdin: $(inputs.text.path)
inputs:
  text:
    type: File
    doc: The text file to count, e.g., at an https URL.
outputs:
  counts:
    type: stdout
    doc: The numbers of lines, words and characters.
stdout: counts.txt
