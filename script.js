/*
 * Shared utility functions for the aptitude timer static site.
 * All data is stored in localStorage.  Passwords are stored in
 * plain text for simplicity; in a real application you should
 * hash them.  Each user has their own list of timers saved
 * under the key `timers_<username>`.
 */

// Retrieve registered users from localStorage
function getUsers() {
  const usersJson = localStorage.getItem('users');
  return usersJson ? JSON.parse(usersJson) : [];
}

// Save the users array back to localStorage
function setUsers(users) {
  localStorage.setItem('users', JSON.stringify(users));
}

// Find a user by username
function findUser(username) {
  return getUsers().find(u => u.username === username);
}

// Register a new user. Returns true on success or false if the user exists
function registerUser(username, password) {
  const users = getUsers();
  if (users.some(u => u.username === username)) {
    return false;
  }
  users.push({ username, password });
  setUsers(users);
  return true;
}

// Attempt to authenticate a user. Returns true if credentials match
function authenticateUser(username, password) {
  const user = findUser(username);
  if (!user) return false;
  return user.password === password;
}

// Get timers for a specific user
function getTimers(username) {
  const key = `timers_${username}`;
  const timersJson = localStorage.getItem(key);
  return timersJson ? JSON.parse(timersJson) : [];
}

// Save timers list for a user
function setTimers(username, timers) {
  const key = `timers_${username}`;
  localStorage.setItem(key, JSON.stringify(timers));
}

// Add a new timer for a user
function addTimer(username, name, minutes) {
  const timers = getTimers(username);
  const id = Date.now();
  timers.push({ id, name, minutes: parseInt(minutes, 10) });
  setTimers(username, timers);
  return id;
}

// Add a new multi-section timer (sequence) for a user. Each segment should be an object
// with `name` and `minutes` properties. The total minutes is computed by summing
// segment durations. Saved timers with segments will run sequentially when started.
function addSequenceTimer(username, name, segments) {
  const timers = getTimers(username);
  const id = Date.now();
  // compute total minutes
  const total = segments.reduce((sum, seg) => sum + parseInt(seg.minutes, 10), 0);
  timers.push({ id, name, minutes: total, segments });
  setTimers(username, timers);
  return id;
}

// Find timer by id for a user
function findTimer(username, id) {
  const timers = getTimers(username);
  return timers.find(t => t.id === id);
}

// Remove timer by id for a user
function removeTimer(username, id) {
  let timers = getTimers(username);
  timers = timers.filter(t => t.id !== id);
  setTimers(username, timers);
}