import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '10s', target: 250 },  // Ramp-up to 250 users in 10 seconds
    { duration: '20s', target: 1000 }, // Stay at 1000 users for 20 seconds
    { duration: '10s', target: 0 },    // Ramp-down to 0 users in 10 seconds
  ],
};

export default function () {
  let res = http.get('https://chfwhitehats2024.games/#/results/67c56dfbf38f54ade6894c69?redirect=true');
  
  check(res, {
    'is status 200': (r) => r.status === 200,
  });
  
  sleep(1);
}
