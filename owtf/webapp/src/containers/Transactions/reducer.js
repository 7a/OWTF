import { fromJS } from 'immutable';
import { combineReducers } from 'redux-immutable'; // combineReducers of 'redux' doesn't work with immutable.js

import {
  LOAD_TARGETS,
  LOAD_TARGETS_SUCCESS,
  LOAD_TARGETS_ERROR,
  LOAD_TRANSACTIONS,
  LOAD_TRANSACTIONS_SUCCESS,
  LOAD_TRANSACTIONS_ERROR,
  LOAD_TRANSACTION,
  LOAD_TRANSACTION_SUCCESS,
  LOAD_TRANSACTION_ERROR,
} from './constants';


// The initial state of the targets.
const initialTargetsState = fromJS({
  loading: false,
  error: false,
  targets: false,
});

function targetsLoadReducer(state = initialTargetsState, action) {
  switch (action.type) {
    case LOAD_TARGETS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('targets', false);
    case LOAD_TARGETS_SUCCESS:
      return state
        .set('loading', false)
        .set('targets', action.targetsData.data);
    case LOAD_TARGETS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the transactions.
const initialTransactionsState = fromJS({
  loading: false,
  error: false,
  transactions: false,
});

function transactionsLoadReducer(state = initialTransactionsState, action) {
  switch (action.type) {
    case LOAD_TRANSACTIONS:
      return state
        .set('loading', true)
        .set('error', false)
        .set('transactions', false);
    case LOAD_TRANSACTIONS_SUCCESS:
      return state
        .set('loading', false)
        .set('transactions', action.transactions);
    case LOAD_TRANSACTIONS_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

// The initial state of the transaction.
const initialTransactionState = fromJS({
  loading: false,
  error: false,
  transaction: false,
});

function transactionLoadReducer(state = initialTransactionState, action) {
  switch (action.type) {
    case LOAD_TRANSACTION:
      return state
        .set('loading', true)
        .set('error', false)
        .set('transaction', false);
    case LOAD_TRANSACTION_SUCCESS:
      return state
        .set('loading', false)
        .set('transaction', action.transaction);
    case LOAD_TRANSACTION_ERROR:
      return state
        .set('loading', false)
        .set('error', action.error);
    default:
      return state;
  }
}

export default combineReducers({
  loadTargets: targetsLoadReducer,
  loadTransactions: transactionsLoadReducer,
  loadTransaction: transactionLoadReducer,
})
