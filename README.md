# Geocaching-Review-Documents
A public repo of some Geocaching reviewer documents and scripts that I've created.

## Convert `clippings.html` into markdown files

Use the conversion script to generate one markdown file per subheading:

```bash
python3 convert_clippings.py <input-clippings.html> --output-dir <output-directory>
```

The generated files use this naming format:

`<Primary-Heading>--<Subheading>.md`

Special characters are removed (except `-` and `_`), spaces become `-`, and heading/subheading are separated with `--`.
