SHELL := /bin/sh

APP_NAME := suviewer
APPIMAGE_NAME := SUviewer-$(shell uname -m).AppImage
APPDIR := AppDir
DIST_BINARY := dist/$(APP_NAME)
SPEC := $(APP_NAME).spec
ICON_URL := https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f30a.png
APPIMAGETOOL_URL := https://github.com/AppImage/appimagetool/releases/latest/download/appimagetool-x86_64.AppImage

.PHONY: all help build appdir icon appimage deploy clean

all: appimage

help:
	@printf '%s\n' \
		"make build     Build the PyInstaller executable" \
		"make appdir    Populate AppDir" \
		"make appimage  Build the AppImage" \
		"make deploy    Build the complete AppImage" \
		"make clean     Remove generated build artifacts"

build:
	python3 -m PyInstaller --clean --noconfirm $(SPEC)

icon:
	@if command -v wget >/dev/null 2>&1; then \
		wget -q -O $(APPDIR)/$(APP_NAME).png $(ICON_URL); \
	elif command -v curl >/dev/null 2>&1; then \
		curl -fL -o $(APPDIR)/$(APP_NAME).png $(ICON_URL); \
	else \
		printf '%s\n' 'Error: install wget or curl to download the icon.' >&2; \
		exit 1; \
	fi

appdir: build
	mkdir -p $(APPDIR)/usr/bin
	printf '%s\n' \
		'#!/bin/sh' \
		'DIR=$$(CDPATH= cd -- "$$(dirname -- "$$0")" && pwd)' \
		'exec "$$DIR/usr/bin/$(APP_NAME)" "$$@"' \
		> $(APPDIR)/AppRun
	printf '%s\n' \
		'[Desktop Entry]' \
		'Name=DiffSeis SU Viewer' \
		'Comment=View Seismic Unix files' \
		'Exec=$(APP_NAME)' \
		'Icon=$(APP_NAME)' \
		'Terminal=false' \
		'Type=Application' \
		'Categories=Science;' \
		> $(APPDIR)/$(APP_NAME).desktop
	cp $(DIST_BINARY) $(APPDIR)/usr/bin/$(APP_NAME)
	chmod +x $(APPDIR)/AppRun $(APPDIR)/usr/bin/$(APP_NAME)
	$(MAKE) icon

appimage: appdir
	@if [ ! -x ./appimagetool ]; then \
		if command -v wget >/dev/null 2>&1; then \
			wget -q -O appimagetool $(APPIMAGETOOL_URL); \
		elif command -v curl >/dev/null 2>&1; then \
			curl -fL -o appimagetool $(APPIMAGETOOL_URL); \
		else \
			printf '%s\n' 'Error: install wget or curl to download appimagetool.' >&2; \
			exit 1; \
		fi; \
		chmod +x appimagetool; \
	fi
	./appimagetool --appimage-extract-and-run $(APPDIR) $(APPIMAGE_NAME)

deploy: appimage

clean:
	rm -rf build dist $(APPIMAGE_NAME) AppDir appimagetool 
