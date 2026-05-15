// Setup jsdom for browser API simulation
import { JSDOM } from 'jsdom';
import fetch from 'node-fetch';

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost'
});

// Setup globals pointing to jsdom's window
global.window = dom.window;
global.document = dom.window.document;
global.XMLHttpRequest = dom.window.XMLHttpRequest;

// Add fetch to window - this is what spyOn will intercept
global.window.fetch = fetch;

// Make bare fetch() calls resolve to window.fetch through a proxy
global.fetch = (...args) => global.window.fetch(...args);
