package net.gbmvdd.bank.ui.client;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

import org.eclipse.swt.custom.CBanner;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.DomEvent;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.dom.client.KeyUpEvent;
import com.google.gwt.event.dom.client.KeyUpHandler;
import com.google.gwt.event.shared.GwtEvent;
import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.RequestException;
import com.google.gwt.http.client.Response;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Event;
import com.google.gwt.user.client.rpc.AsyncCallback;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.DialogBox;
import com.google.gwt.user.client.ui.FlexTable;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HTMLTable;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.RadioButton;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Widget;

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
  
  // Create a handler for the sendButton and nameField
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
      int row = Integer.parseInt(id.substring(id.indexOf('-') + 1));
      CheckBox checkBox = ((CheckBox) transactionsTable.getWidget(row, 0));
      Boolean selected = checkBox.getValue();
      String fitid = checkBox.getFormValue();
      if (selected) {
        transactionSelection.add(fitid);
      } else {
        transactionSelection.remove(fitid);
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
            Transaction transaction = records.get(i);

            CheckBox checkBox = new CheckBox();
            checkBox.getElement().setId("transaction-" + i);
            checkBox.setFormValue(transaction.getFitId());
            transactionsTable.setWidget(i, 0, checkBox);
            transactionsTable.setText(i, 1, transaction.getDate());
            transactionsTable.setText(i, 2, transaction.getAmount());
            transactionsTable.setText(i, 3, transaction.getMemo());
            checkBox.addClickHandler(onTransactionSelectionChanged);
          }
        }
      });
    } catch (RequestException e) {
      handleException(e);
    }
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

  public static <T extends JavaScriptObject> JsArray<T> getJsonArray(Response response) {
    JSONArray results = (JSONArray) JSONParser.parse(response
        .getText());
    @SuppressWarnings("unchecked")
    JsArray<T> records = (JsArray<T>) results .getJavaScriptObject();
    return records;
  }
}
