SCHEMA := ClinVar_VCV_2.6.xsd
TRANSFORMS := clinvar_transforms.yaml
GENERATED_DIR := generated

.PHONY: generate build clean

# Generate the package source tree from the XSD + transforms config.
# namespace / package_name / version come from the build: section of $(TRANSFORMS).
generate: $(SCHEMA) $(TRANSFORMS)
	uv run xsdformer build $(SCHEMA) \
		--transforms $(TRANSFORMS) \
		--out-dir $(GENERATED_DIR)

# Build a wheel from the generated source tree.
build: generate
	cd $(GENERATED_DIR) && uv build --out-dir ../dist

clean:
	rm -rf $(GENERATED_DIR) dist
