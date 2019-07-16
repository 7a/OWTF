import Request from "../../utils/request";
import { API_BASE_URL } from "../../utils/constants";

export function getErrorsAPI() {
  const requestURL = `${API_BASE_URL}errors/`;
  // Call our request helper (see 'utils/request')
  const request = new Request(requestURL);
  return request.get.bind(request);
}

export function postErrorAPI() {
  const requestURL = `${API_BASE_URL}errors/`;
  const options = {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  };
  const request = new Request(requestURL, options);
  return request.post.bind(request);
}

export function deleteErrorAPI(action) {
  const error_id = action.error_id.toString();
  const requestURL = `${API_BASE_URL}errors/${error_id}/`;

  const request = new Request(requestURL);
  return request.delete.bind(request);
}
