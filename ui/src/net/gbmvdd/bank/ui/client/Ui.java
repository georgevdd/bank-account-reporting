package net.gbmvdd.bank.ui.client;

import java.util.HashSet;
import java.util.Set;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.DomEvent;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.dom.client.KeyUpEvent;
import com.google.gwt.event.dom.client.KeyUpHandler;
import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.RequestException;
import com.google.gwt.http.client.Response;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.RadioButton;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;
import com.google.gwt.user.client.ui.HTMLTable.RowFormatter;

public class Ui implements EntryPoint {
  /**
   * The message displayed to the user when the server cannot be reached or
   * returns an error.
   */
  private static final String SERVER_ERROR = "An error occurred while "
      + "attempting to contact the server. Please check your network "
      + "connection and try again.";

  private Grid statementsTable;
  private Grid transactionsTable;

  private StatementChosenHandler onStatementChosen = new StatementChosenHandler();
  private ClickHandler onTransactionSelectionChanged = new TransactionSelectionChangedHandler();
  
  private Set<String> transactionSelection;

  /**
   * This is the entry point method.
   */
  public void onModuleLoad() {
    statementsTable = new Grid();
    transactionsTable = new Grid();
    statementsTable.addStyleName("row");
    transactionsTable.addStyleName("row");
    
    Button paymentButton = new Button();
    paymentButton.setText("Mark as Payment");
    
    Button invoiceableButton = new Button();
    invoiceableButton.setText("Mark as Invoiceable");

    RootPanel.get("statementContainer").add(statementsTable);
    RootPanel.get("transactionContainer").add(transactionsTable);
    RootPanel buttonContainer = RootPanel.get("actionContainer");
    buttonContainer.add(invoiceableButton);
    buttonContainer.add(invoiceableButton);
    
    fetchStatements();
  }
  
  // Create a handler for the sendButton and nameField
  private class StatementChosenHandler implements ClickHandler, KeyUpHandler {
    public void onClick(ClickEvent event) {
      adjustSelection(event);
    }

    public void onKeyUp(KeyUpEvent event) {
      if (event.getNativeKeyCode() == KeyCodes.KEY_ENTER) {
        adjustSelection(event);
      }
    }

    private void adjustSelection(DomEvent event) {
      transactionSelection = new HashSet<String>();
      
      String id = ((Widget) event.getSource()).getElement().getId();
      int row = Integer.parseInt(id.substring(id.indexOf('-') + 1));
      String startDate = statementsTable.getText(row, 1);
      String endDate = statementsTable.getText(row, 2);
      fetchTransactions(startDate, endDate);
    }
  }

  private class TransactionSelectionChangedHandler implements ClickHandler, KeyUpHandler {
    public void onClick(ClickEvent event) {
      adjustSelection(event);
    }

    public void onKeyUp(KeyUpEvent event) {
      if (event.getNativeKeyCode() == KeyCodes.KEY_ENTER) {
        adjustSelection(event);
      }
    }

    private void adjustSelection(DomEvent event) {
      String id = ((Widget) event.getSource()).getElement().getId();
      final int row = Integer.parseInt(id.substring(id.indexOf('-') + 1));
      CheckBox checkBox = ((CheckBox) transactionsTable.getWidget(row, 0));
      Boolean selected = checkBox.getValue();
      String fitid = checkBox.getFormValue();

      Transaction transaction = Transaction.createObject().cast();
      transaction.setFitId(fitid);
      transaction.setIsInvoiceable(selected);
      
      RequestBuilder rb = new RequestBuilder(
          RequestBuilder.POST, "/data/transactions/update/" + fitid);
      rb.setHeader("Content-Type", "application/x-www-form-urlencoded");
      String requestData =
          "data=" + transaction.toJSON()
          + "&_method=PUT";
      try {
        rb.sendRequest(requestData, new RequestCallback() {

          public void onError(Request request, Throwable exception) {
            handleException(exception);
          }

          public void onResponseReceived(Request request, Response response) {
            setUpRowForTransaction(transactionsTable, row,
                Ui.<Transaction>getJson(response));
          }});
      } catch (RequestException e) {
        handleException(e);
      }
    }
  }

  private void fetchStatements() {
    RequestBuilder rb = new RequestBuilder(RequestBuilder.GET, "/data/statements");
    try {
      rb.sendRequest("", new RequestCallback() {
        public void onError(Request request, Throwable exception) {
          handleException(exception);
        }

        public void onResponseReceived(Request request, Response response) {
          @SuppressWarnings("unchecked")
          JsArray<Statement> records = getJsonArray(response);
          statementsTable.resize(records.length(), 3);
          for (int i = 0; i < records.length(); ++i) {
            RadioButton radioButton = new RadioButton("statement");
            radioButton.getElement().setId("statement-" + i);
            statementsTable.setWidget(i, 0, radioButton);
            statementsTable.setText(i, 1, records.get(i).getBeginDate());
            statementsTable.setText(i, 2, records.get(i).getEndDate());
            radioButton.addClickHandler(onStatementChosen);
          }
        }
      });
    } catch (RequestException e) {
      handleException(e);
    }

  }

  private void fetchTransactions(String startDate, String endDate) {
    RequestBuilder rb = new RequestBuilder(RequestBuilder.GET,
        "/data/transactions?" +
            "startDate=" + startDate + "&" +
            "endDate=" + endDate);
    try {
      rb.sendRequest("", new RequestCallback() {
        public void onError(Request request, Throwable exception) {
          handleException(exception);
        }

        public void onResponseReceived(Request request, Response response) {
          @SuppressWarnings("unchecked")
          JsArray<Transaction> records = getJsonArray(response);
          transactionsTable.resize(records.length(), 4);
          for (int i = 0; i < records.length(); ++i) {
            setUpRowForTransaction(transactionsTable, i, records.get(i));
          }
        }
      });
    } catch (RequestException e) {
      handleException(e);
    }
  }

  private void setUpRowForTransaction(Grid table, int i,
      Transaction transaction) {
    CheckBox checkBox = new CheckBox();
    checkBox.getElement().setId("transaction-" + i);
    checkBox.setFormValue(transaction.getFitId());
    checkBox.setValue(transaction.isInvoiceable());
    table.setWidget(i, 0, checkBox);
    table.setText(i, 1, transaction.getDate());
    table.setText(i, 2, transaction.getAmount());
    table.setText(i, 3, transaction.getMemo());
    String styleName;
    if (transaction.isLikelyInvoiceable()) {
      styleName = "likelyInvoiceable";
    } else if (transaction.isLikelyPayment()) {
      styleName = "likelyPayment";
    } else {
      styleName = "";
    }
    RowFormatter rowFormatter = table.getRowFormatter();
    rowFormatter.setStyleName(i, styleName);
    checkBox.addClickHandler(onTransactionSelectionChanged);
  }

  private void handleException(Throwable e) {
    // ByteArrayOutputStream bytes = new ByteArrayOutputStream();
    // e.printStackTrace(new PrintStream(bytes));
    //              dialogBox.setText(bytes.toString());
    e.printStackTrace();

    // Create the popup dialog box
    final DialogBox dialogBox = new DialogBox();
    dialogBox.setText("Remote Procedure Call");
    dialogBox.setAnimationEnabled(true);
    final Button closeButton = new Button("Close");

    // We can set the id of a widget by accessing its Element
    closeButton.getElement().setId("closeButton");
    // Add a handler to close the DialogBox
    closeButton.addClickHandler(new ClickHandler() {
      public void onClick(ClickEvent event) {
        dialogBox.hide();
      }
    });

    final HTML serverResponseLabel = new HTML();
    serverResponseLabel.setText(e.getMessage());

    VerticalPanel dialogVPanel = new VerticalPanel();
    dialogVPanel.addStyleName("dialogVPanel");
    dialogVPanel.add(new HTML("<br><b>Error:</b>"));
    dialogVPanel.add(serverResponseLabel);
    dialogVPanel.setHorizontalAlignment(VerticalPanel.ALIGN_RIGHT);
    dialogVPanel.add(closeButton);
    dialogBox.setWidget(dialogVPanel);

    dialogBox.setTitle(e.toString());
    dialogBox.setText("Sorry!");
  }
  
  @SuppressWarnings("unchecked")
  public static <T extends JavaScriptObject> T getJson(Response response) {
    JSONObject result = (JSONObject) JSONParser.parse(response.getText());
    return (T) result.getJavaScriptObject();
  }

  public static <T extends JavaScriptObject> JsArray<T> getJsonArray(Response response) {
    JSONArray results = (JSONArray) JSONParser.parse(response
        .getText());
    @SuppressWarnings("unchecked")
    JsArray<T> records = (JsArray<T>) results.getJavaScriptObject();
    return records;
  }
}
