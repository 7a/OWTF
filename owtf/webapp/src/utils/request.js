/**
 *
 * Request.js
 *
 * This file contains a util functions to make network requests.
 */
import 'whatwg-fetch';

/**
 * Requests a URL, returning a promise
 *
 * @param  {string} url       The URL we want to request
 * @param  {object} [options] The options we want to pass to "fetch"
 *
 * @return {object}           The response promise
 */
export default class Request {

  constructor(url, options) {
    this._url = url;
    this._options = (options === undefined) ? {} : options;
  }

  /**
   * Parses the Response returned by a network request
   *
   * @param  {string} type Format in which response is required.
   * @param  {object} response A response from a network request
   *
   * @return {object} The parsed data in required format from the request
   */
  static _parseResponse(type, response) {
    if (response.status === 204 || response.status === 205) {
      return null;
    }
    return (type === "json") ? response.json() : response.text();
  }

  /**
   * Checks if a network request came back fine, and throws an error if not
   *
   * @param  {object} response   A response from a network request
   *
   * @return {object|undefined} Returns either the response, or throws an error
   */
  static _checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
      return response;
    }

    const error = new Error(response.statusText);
    error.response = response;
    throw error;
  }

  /**
   * Converts parameters from GET request to append in URL.
   *
   * @param  {object} queryParams Query parameters.
   *
   * @return {string} string to append in URL.
   */

  _getQuery (queryParams) {
    const arr = Object.keys(queryParams).map(k => `${k}=${encodeURIComponent(queryParams[k])}`);
    return `?${arr.join('&')}`
  }

  /**
   * Adds default headers for request if not passed by saga.
   *
   * @param  {object} target Object in which we are adding default headers.
   * @param  {object} headers Default headers to add.
   */

  static _addDefaults (target, headers) {
    for (const prop in headers) {
      target[prop] = target[prop] || headers[prop];
    }
  }

  /**
   * Requests a URL, returning a promise
   *
   * @param  {string} method HTTP Method of request.
   * @param  {string} url URL of request.
   * @param  {object} opts optional headers.
   * @param  {object} data Data to submit. Required by POST, PATCH, DELETE, PUT requests.
   * @param  {object} queryParams Query Parameters for GET requests.
   *
   * @return {object} The response data.
   */

  _fetch (method, url, opts, data = null, queryParams = null) {
    opts.method = method;
    opts.headers = opts.headers || {};
    opts.responseAs = (opts.responseAs && ['json', 'text'].includes(opts.responseAs)) ? opts.responseAs : 'json';

    Request._addDefaults(opts.headers, {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    });

    if (queryParams) {
      url += this._getQuery(queryParams)
    }

    if (data) {
      opts.body = JSON.stringify(data);
    } else {
      delete opts.body;
    }

    return fetch(url, opts)
      .then(Request._checkStatus)
      .then(Request._parseResponse.bind(null, opts.responseAs));
  }

  /**
   * Method to make GET requests.
   *
   * @param  {object} queryParams Query Parameters for GET requests.
   *
   * @return {object} The response data.
   */

  get(queryParams) {
    return this._fetch('GET', this._url, this._options, null, queryParams);
  }

  /**
   * Method to make POST requests.
   *
   * @param  {object} data Data to submit. Required by POST, PATCH, DELETE, PUT requests.
   *
   * @return {object} The response data.
   */

  post(data) {
    return this._fetch('POST', this._url, this._options, data)
  }

  /**
   * Method to make PATCH requests.
   *
   * @param  {object} data Data to submit.
   *
   * @return {object} The response data.
   */

  patch(data) {
    return this._fetch('PATCH', this._url, this._options, data)
  }

  /**
   * Method to make PUT requests.
   *
   * @param  {object} data Data to submit.
   *
   * @return {object} The response data.
   */

  put(data) {
    return this._fetch('PUT', this._url, this._options, data)
  }

  /**
   * Method to make DELETE requests.
   *
   * @return {object} The response data.
   */

  delete() {
    return this._fetch('DELETE', this._url, this._options)
  }

}
