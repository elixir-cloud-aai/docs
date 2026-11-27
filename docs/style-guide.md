---
hide:
  - feedback
---

# Style Guide

This page is for people who write or change pages of the Documentation Hub.
Follow it so that every page looks and reads the same. To edit and build the
docs, see the
[README](https://github.com/elixir-cloud-aai/docs/blob/main/README.md).

## Language

- Use simple words and short sentences. One idea per sentence.
- Address the reader as "you". Use the active voice and the imperative for
  steps: "Open the form", not "The form should be opened".
- Use one name per thing, as the [Glossary](glossary.md) spells it. If a
  term is missing there, add it in the same pull request.
- Spell the project names "ELIXIR On-Cloud", "ELIXIR" and "ELIXIR Europe"
  (`python scripts/check_names.py` checks this).
- Write for the audience of the section: architects and operators, partners
  and developers, or researchers. Say who a page is for in its intro.
- Write dates as "2026-11-26" or "November 2026". Mark facts that change
  with "As of November 2026" and the `last_verified` date (see the README).

## Page layout

Every page has one purpose and follows this order. Leave out a part that
doesn't apply.

1. **Title:** one `#` heading, the same as its label in the navigation
   (except Home, whose page is titled "Welcome").
2. **Intro:** what the page is, who it is for and what the reader gets, in
   a few sentences.
3. **Prerequisites:** what the reader needs before they start (accounts,
   access, tools), as a list.
4. **Steps:** numbered, one action each, with the command or the click and
   the result to expect. Use `##` headings for parts.
5. **What's next:** links to the pages that follow, and where to ask.

Link to another page instead of repeating it. The link text says where the
link leads ("see [Onboarding](operators/onboarding.md)"), never "here".

## Admonitions

Use them sparingly, with a title in quotes:

```markdown
!!! note "Title"
    Extra information that helps, but isn't needed to follow the steps.

!!! warning "Title"
    Something that can break a setup, leak a secret or lose data.
```

- `note`: background or a limit.
- `warning`: danger. Name the consequence.

Don't put steps in an admonition. Section start pages include the scope
note with `--8<-- "includes/scope.md"`.

## Code blocks

- Always name the language: `sh`, `yaml`, `json`, `python` or `markdown`.
- Use placeholders in capitals in angle brackets, for example `<HOST>`, and
  say what each one is. Use `example.org` for example addresses.
- Put one command in a step where possible, and show the output to expect
  after it.
- Never put secrets, tokens or personal data in a code block.
- Use `inline code` for commands, file names, field names, group names and
  addresses.

## Tables

Use a table for facts that have the same shape (what, value, link), not for
steps or prose. Give every column a header, keep cells short and put one
fact in a cell. For the services in the Cloud Registry, use the marker
`<!-- registry:services -->` instead of a handwritten table (see the
README).

## Navigation

- Every page is in `nav:` of `mkdocs.yml`, once, under the audience that
  needs it, with the title of its `#` heading as the label.
- Every audience section has an `index.md` that says what the section is
  for and links to each of its pages. About groups the pages about the hub
  itself, starting with `about.md`.
- Add a new page in the same pull request as the links to it.

## Before you open a pull request

```sh
python scripts/check_names.py
mkdocs build --strict
```
