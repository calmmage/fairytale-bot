# todos - main features, flow


Hi! This is a fairytale generator bot
- [ ] /randomize    
  - [ ] add usage tracking
  - [ ] add usage checking
  - [ ] add a fancy "here's a story about"

- [ ]/begin - start a new story
    - [ ] build!!!


- [x] /continue - generate next part of the story
  - [ ] check if this is the first part of the story and if so - notify user and start a new story instead
- [ ] /reset - reset the current story and start over
  - [ ] test main scenario (when started a story)
  - [ ] test archive
  - [ ] auto-begin the new story
- [ ] /regenerate - regenerate the current part of the story
  - [ ] build
  - [ ] test
- [ ] /upgrade or /downgrade
  - [ ] test that this works... 
  - [ ] extend functionality
    - [ ] add fake payment / subscription filter
    - [ ] allow admins to upgrade/downgrade users
      - [ ] receive and use a 'user' parameter

- [ ] /help to get a full list of possible commands
  - [ ] main commands - their docstrings
  - [ ] fix commands descriptions (only use the first line)

- [ ] get the story structure

- [ ] try using redis as a storage

- [ ] keep telling the story if the user really wants to?
  result += "Psst.. /sequel command is in development. Don't tell anyone!"]
