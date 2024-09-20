if test -f "./study_data/" ; then
  printf "Data has already been unpacked to ./study_data/, skipping.\n"
else
  printf "Unpacking study_data.7z to ./study_data/. Will result in ~1.1GB.\n"
  7z x study_data.7z -o./study_data/
fi
