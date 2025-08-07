#!/bin/bash

ARGS=("$@")

# Checks if a flag is present in the arguments.
hasflag() {
  for var in "${ARGS[@]}"; do
    if [ "$var" = "$1" ]; then
      echo 'true'
      return
    fi
  done
  echo 'false'
}

# Read the value of an option.
readopt() {
  local target_flag="$1"
  local found_flag=false

  for var in "${ARGS[@]}"; do
    if [[ "$found_flag" = true ]]; then
      # Previous iteration found the flag, this should be the value
      if [[ "$var" != -* ]]; then
        echo "$var"
        return
      else
        # Next arg is another flag, so no value provided
        return
      fi
    fi

    # Check if current arg matches the target flag
    if [[ "$var" = "$target_flag" ]]; then
      found_flag=true
    fi
  done

  # Nothing found
  echo ""
}

# Validate that only --directory flag is used
i=0
while [ $i -lt ${#ARGS[@]} ]; do
  arg="${ARGS[$i]}"
  if [[ "$arg" == --* ]]; then
    if [ "$arg" != "--directory" ]; then
      echo "Only flag allowed is --directory, got '$arg'"
      exit 1
    fi
    # Skip the next argument (the value)
    ((i++))
  fi
  ((i++))
done

DIRECTORY=""
if [ "$(hasflag --directory)" = "true" ]; then
  DIRECTORY=$(readopt --directory)
fi

base_url="https://github.com/official-stockfish/Stockfish/releases/latest/download"

# Download and execute the official Stockfish script, capture the output
output=$(curl -fsSL "https://raw.githubusercontent.com/official-stockfish/Stockfish/master/scripts/get_native_properties.sh" | sh -s)

# Extract the second string from the output to set the file_name variable
file_name=$(echo "$output" | cut -d ' ' -f2)

# Download the file with retry mechanism
echo "Downloading '$base_url/$file_name' to $(pwd)/$DIRECTORY"
if ! curl -fJLO --retry 5 --retry-delay 5 --retry-all-errors "$base_url/$file_name" --create-dirs --output-dir "$DIRECTORY"; then
  echo "Download failed after 5 attempts.\n"
  exit 1
fi

TAR_FILE="${file_name%.tar}"

tar -xvf "$DIRECTORY/$file_name" -C "$(pwd)/$DIRECTORY"
cp "$DIRECTORY/stockfish/$TAR_FILE" "$DIRECTORY/$TAR_FILE"
rm -r "$DIRECTORY/stockfish"
rm "$DIRECTORY/$file_name"

printf 'Done.\n'
